import sys

import requests
from flask import current_app
from requests import RequestException
from sqlalchemy.orm.exc import NoResultFound

from ejudge_listener import create_app
from ejudge_listener.models import EjudgeRun
from ejudge_listener.models import db
from ejudge_listener.plugins import mongo, rq
from ejudge_listener.protocol.protocol import get_full_protocol
from ejudge_listener.schemas import EjudgeRunSchema

# TODO: Add doc.
NON_TERMINAL_RUN_STATUSES = {96, 98}


run_schema = EjudgeRunSchema()


def process_and_send_run(contest_id: int, run_id: int, json: dict = None) -> None:
    app = create_app()
    with app.app_context():
        if json:
            send_run(contest_id, run_id, json)
        else:
            data = process_run(contest_id, run_id)
            send_run(contest_id, run_id, data)


def send_run(contest_id: int, run_id: int, json: dict):
    try:
        r = requests.post('ejudge-front', json=json, timeout=3)
        r.raise_for_status()
    except RequestException:
        log_msg = 'Ejudge-front bad response or timeout, task requeued'
        current_app.logger.exception(log_msg)
        q = rq.get_queue()
        if json['status'] in NON_TERMINAL_RUN_STATUSES:
            q.enqueue(process_and_send_run, contest_id, run_id, None)
        else:
            q.enqueue(process_and_send_run, contest_id, run_id, json)
    log_msg = f'Run with contest_id={contest_id}, run_id={run_id} sended successfully'
    current_app.logger.info(log_msg)


def process_run(contest_id: int, run_id: int) -> dict:
    try:
        run = (
            db.session.query(EjudgeRun)
            .filter_by(contest_id=contest_id)
            .filter_by(run_id=run_id)
            .one()
        )
    except NoResultFound:
        # Critical error, log and exit. Usually we already have run in database.
        log_msg = f'Run with contest_id={contest_id}, run_id={run_id} doesn\'t exist'
        current_app.logger.exception(log_msg)
        sys.exit(log_msg)
    else:
        protocol_id = put_protocol_to_mongo(run)
        data = run_schema.dump(run).data
        data['protocol_id'] = protocol_id
        return data


def put_protocol_to_mongo(run: EjudgeRun) -> str:
    """
    :return: hex encoded version of ObjectId.
    """
    protocol = get_full_protocol(run)
    protocol_id = mongo.db.protocol.insert_one(protocol).inserted_id
    return str(protocol_id)
