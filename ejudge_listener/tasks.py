import functools
import logging
import sys
from time import sleep
from typing import Optional

import requests
from bson import ObjectId
from flask import current_app
from sqlalchemy.orm import joinedload

from ejudge_listener import create_app, init_logger
from ejudge_listener.exceptions import ProtocolNotFoundError
from ejudge_listener.extensions import mongo, rq
from ejudge_listener.models import db
from ejudge_listener.models.ejudge_run import EjudgeRun
from ejudge_listener.protocol.protocol import read_protocol
from ejudge_listener.protocol.run_statuses import TERMINAL_RUN_STATUSES
from ejudge_listener.requests import EjudgeRequest
from ejudge_listener.schemas import EjudgeRunSchema, EjudgeRequestSchema
from ejudge_listener.utils import make_log_message

run_schema = EjudgeRunSchema()
ejudge_request_schema = EjudgeRequestSchema()


def send_to_front(ej_request: EjudgeRequest):
    isterminal = ej_request.status in TERMINAL_RUN_STATUSES
    if isterminal:
        send_terminal(ej_request)
    else:
        send_non_terminal(ej_request)


def enqueue_task(func, *args, **kwargs):
    q = rq.get_queue('ejudge_listener')
    q.enqueue(func, *args, **kwargs)


def send_data_to_front(data):
    r = requests.post(current_app.config['EJUDGE_FRONT_URL'], json=data, timeout=5)
    r.raise_for_status()


def create_app_and_push_context(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        app = create_app()
        with app.app_context():
            return func(*args, **kwargs)

    return wrapper


@create_app_and_push_context
def send_delayed_protocol(ej_request: EjudgeRequest):
    # We sleep 2 seconds because FS may not sync protocol yet
    sleep(2)
    try:
        data = process_run(ej_request)
    except ProtocolNotFoundError:
        logging.exception(
            make_log_message('send_delayed_protocol', 'revoked', ej_request)
        )
        return  # raise ? to put it to failed tasks

    try:
        send_data_to_front(data)
    except requests.HTTPError as e:
        status_code = e.response.status_code
        if is_4xx_error(status_code):
            msg = make_log_message(
                'send_delayed_protocol', 'revoked', ej_request, status_code
            )
            mongo_rollback(data)
        else:
            msg = make_log_message('send_terminal', 'retry', ej_request, status_code)
            enqueue_task(send_delayed_protocol, ej_request, data)
        logging.exception(msg)
    except requests.RequestException:
        logging.exception(
            make_log_message('send_delayed_protocol', 'retry', ej_request)
        )
        enqueue_task(send_delayed_protocol, ej_request, data)
    else:
        logging.info(make_log_message('send_terminal', 'success', ej_request))


@create_app_and_push_context
def send_terminal(ej_request: EjudgeRequest, data: Optional[dict] = None) -> None:
    try:
        data = data or process_run(ej_request)
    except ProtocolNotFoundError:
        # not logging.exception because it ordinary behavior
        logging.error(make_log_message('send_terminal', 'revoked', ej_request))
        enqueue_task(send_delayed_protocol, ej_request)
        return

    try:
        send_data_to_front(data)
    except requests.HTTPError as e:
        status_code = e.response.status_code
        if is_4xx_error(status_code):
            msg = make_log_message('send_terminal', 'revoked', ej_request, status_code)
            mongo_rollback(data)
        else:
            msg = make_log_message('send_terminal', 'retry', ej_request, status_code)
            enqueue_task(send_terminal, ej_request, data)
        logging.exception(msg)
    except requests.RequestException:
        logging.exception(make_log_message('send_terminal', 'retry', ej_request))
        enqueue_task(send_terminal, ej_request, data)
    else:
        logging.info(make_log_message('send_terminal', 'success', ej_request))


@create_app_and_push_context
def send_non_terminal(ej_request: EjudgeRequest) -> None:
    init_logger()
    data = ejudge_request_schema.dump(ej_request).data
    try:
        r = requests.post(current_app.config['EJUDGE_FRONT_URL'], json=data, timeout=5)
        r.raise_for_status()
    except requests.RequestException:
        logging.exception(make_log_message('send_non_terminal', 'revoked', ej_request))
    else:
        logging.info(make_log_message('send_non_terminal', 'success', ej_request))


def process_run(ej_request: EjudgeRequest) -> dict:
    run = (
        db.session.query(EjudgeRun)
        .filter_by(run_id=ej_request.run_id, contest_id=ej_request.contest_id)
        .options(joinedload(EjudgeRun.problem))
        .one_or_none()
    )

    if run is None:
        msg = (
            f'Run with run_id={ej_request.run_id} '
            f'contest_id={ej_request.contest_id}, doesn\'t exist'
        )
        logging.exception(msg)
        sys.exit(0)
    protocol = read_protocol(run)
    mongo.init_app(current_app)
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


def is_4xx_error(status_code) -> bool:
    return 400 <= status_code < 500
