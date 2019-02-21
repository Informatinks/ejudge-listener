import logging
import sys
from typing import Optional

import requests
from bson import ObjectId
from flask import current_app
from requests import RequestException

from ejudge_listener import create_app, init_logger
from ejudge_listener.exceptions import ProtocolNotFoundError
from ejudge_listener.extensions import mongo, rq
from ejudge_listener.models import db
from ejudge_listener.models.ejudge_run import EjudgeRun
from ejudge_listener.protocol.protocol import read_protocol
from ejudge_listener.protocol.run_statuses import TERMINAL_RUN_STATUSES
from ejudge_listener.requests import EjudgeRequest
from ejudge_listener.schemas import EjudgeRunSchema, EjudgeRequestSchema
from ejudge_listener.utils import LogMessage

run_schema = EjudgeRunSchema()
ejudge_request_schema = EjudgeRequestSchema()


def send_to_front(ej_request: EjudgeRequest):
    isterminal = ej_request.status in TERMINAL_RUN_STATUSES
    if isterminal:
        send_terminal(ej_request)
    else:
        send_non_terminal(ej_request)


def send_terminal(ej_request: EjudgeRequest, data: Optional[dict] = None) -> None:
    init_logger()
    app = create_app()
    with app.app_context():
        try:
            data = data or process_run(ej_request)
            r = requests.post(
                current_app.config['EJUDGE_FRONT_URL'], json=data, timeout=5
            )
            r.raise_for_status()
        except ProtocolNotFoundError:
            msg = LogMessage('send_terminal', 'cancel', ej_request)
            logging.exception(str(msg))
        except RequestException as e:
            status_code = e.response.status_code
            if is_client_error(status_code):
                mongo_rollback(data)
                msg = LogMessage('send_terminal', 'cancel', ej_request, status_code)
                logging.exception(str(msg))
            else:
                q = rq.get_queue('ejudge_listener')
                msg = LogMessage('send_terminal', 'retry', ej_request, status_code)
                logging.exception(str(msg))
                q.enqueue(send_terminal, ej_request, data)

        db.session.rollback()


def send_non_terminal(ej_request: EjudgeRequest) -> None:
    init_logger()
    data = ejudge_request_schema.dump(ej_request).data
    try:
        r = requests.post(current_app.config['EJUDGE_FRONT_URL'], json=data, timeout=5)
        r.raise_for_status()
    except requests.RequestException:
        msg = LogMessage('send_non_terminal', 'cancel', ej_request)
        logging.exception(str(msg))
    else:
        msg = LogMessage('send_non_terminal', 'done', ej_request)
        logging.info(str(msg))


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
        logging.exception(msg)
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


def mongo_rollback(data: dict) -> None:
    mongo_id = data['mongo_protocol_id']
    mongo.db.protocol.delete_one({'_id', ObjectId(mongo_id)})


def is_client_error(status_code) -> bool:
    return 400 <= status_code < 500
