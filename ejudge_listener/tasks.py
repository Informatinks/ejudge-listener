import sys

import requests
from flask import current_app
from requests import RequestException
from sqlalchemy.orm.exc import NoResultFound

from ejudge_listener import create_app
from ejudge_listener.models import db, EjudgeRun
from ejudge_listener.plugins import mongo, rq
from ejudge_listener.protocol.protocol import get_full_protocol
from ejudge_listener.protocol.run_statuses import TERMINAL_RUN_STATUSES
from ejudge_listener.schemas import EjudgeRunSchema

run_schema = EjudgeRunSchema()


def send_run(contest_id: int, run_id: int, json: dict = None) -> None:
    app = create_app()
    with app.app_context():
        if json:
            send_json_to_front(contest_id, run_id, json)
        else:
            data = process_run(contest_id, run_id)
            send_json_to_front(contest_id, run_id, data)


def send_json_to_front(contest_id: int, run_id: int, json: dict):
    try:
        r = requests.post('ejudge-front', json=json, timeout=3)
        r.raise_for_status()
    except RequestException:
        log_msg = 'Ejudge-front bad response or timeout, task requeued'
        current_app.logger.exception(log_msg)
        q = rq.get_queue()
        if json['status'] in TERMINAL_RUN_STATUSES:
            q.enqueue(send_run, contest_id, run_id, json)
            return
    log_msg = f'Run with contest_id={contest_id}, run_id={run_id} sended successfully'
    current_app.logger.info(log_msg)


def process_run(contest_id: int, run_id: int) -> dict:
    try:
        run = db.session.query(EjudgeRun) \
              .filter_by(contest_id=contest_id) \
              .filter_by(run_id=run_id) \
              .one()
    except NoResultFound:
        # Critical error, log and exit. Usually we already have run in database.
        db.session.rollback()
        log_msg = f'Run with contest_id={contest_id}, run_id={run_id} doesn\'t exist'
        current_app.logger.exception(log_msg)
        sys.exit(0)
    mongo_protocol_id = put_protocol_to_mongo(run)
    run.mongo_protocol_id = mongo_protocol_id
    data = run_schema.dump(run).data
    return data


def put_protocol_to_mongo(run: EjudgeRun) -> str:
    """
    :return: hex encoded version of ObjectId.
    """
    protocol = get_full_protocol(run)
    protocol_id = mongo.db.protocol.insert_one(protocol).inserted_id
    return str(protocol_id)
