import sys

import requests
from flask import current_app

from ejudge_listener import create_app
from ejudge_listener.exceptions import ProtocolNotFoundError
from ejudge_listener.extensions import mongo, rq
from ejudge_listener.models import db
from ejudge_listener.models.ejudge_run import EjudgeRun
from ejudge_listener.protocol.protocol import read_protocol
from ejudge_listener.requests import EjudgeRequest
from ejudge_listener.schemas import EjudgeRunSchema, EjudgeRequestSchema

run_schema = EjudgeRunSchema()
ejudge_request_schema = EjudgeRequestSchema()


def send_terminal_to_front(ej_request: EjudgeRequest, data: dict = None) -> None:
    app = create_app()
    with app.app_context():
        try:
            if not data:
                data = process_run(ej_request)
            send_json_to_front(data)
        except ProtocolNotFoundError:
            msg = (
                f'Protocol for run_id={ej_request.run_id} '
                f'contest_id={ej_request.contest_id} not found'
            )
            current_app.logger.exception(msg)
        except requests.RequestException:
            msg = ', task requeued'
            current_app.logger.exception(msg)
            q = rq.get_queue('ejudge_listener')
            q.enqueue(send_terminal_to_front, ej_request, data)
        db.session.rollback()


def send_non_terminal_to_front(ej_request: EjudgeRequest):
    data = ejudge_request_schema.dump(ej_request).data
    try:
        send_json_to_front(data)
    except requests.RequestException:
        msg = f'Current task with {ej_request!r} cancelled'
        current_app.logger.exception(msg)


def send_json_to_front(json: dict):
    try:
        r = requests.post(current_app.config['EJUDGE_FRONT_URL'], json=json, timeout=5)
    except requests.RequestException as e:
        msg = 'Ejudge-front bad response or timeout'
        current_app.logger.exception(msg)
        raise e
    else:
        run_id = json['run_id']
        contest_id = json['contest_id']
        msg = f'Run with run_id={run_id} contest_id={contest_id} sent successfully'
        current_app.logger.info(msg)


def process_run(ej_request: EjudgeRequest) -> dict:
    run = (
        db.session.query(EjudgeRun)
        .filter_by(run_id=ej_request.run_id, contest_id=ej_request.contest_id)
        .one_or_none()
    )
    if run is None:
        db.session.rollback()
        msg = (
            f'Run with run_id={ej_request.run_id} '
            f'contest_id={ej_request.contest_id}, doesn\'t exist'
        )
        current_app.logger.exception(msg)
        sys.exit(0)
    protocol = read_protocol(run)
    mongo_protocol_id = insert_protocol_to_mongo(protocol)
    run.mongo_protocol_id = mongo_protocol_id
    data = run_schema.dump(run).data
    return data


def insert_protocol_to_mongo(protocol: dict) -> str:
    """
    Insert EjudgeRun protocol to mongo.
    :param protocol: EjudgeRun protocol.
    :return: hex encoded version of ObjectId.
    """
    protocol_id = mongo.db.protocol.insert_one(protocol).inserted_id
    mongo_protocol_id = str(protocol_id)
    return mongo_protocol_id
