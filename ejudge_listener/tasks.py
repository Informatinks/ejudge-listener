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

run_schema = EjudgeRunSchema()


def send_run(contest_id: int, run_id: int, json=None) -> None:
    app = create_app()
    with app.app_context():
        try:
            json = json or form_json(contest_id, run_id)
            r = requests.post('ejudge-front', json=json, timeout=3)
            r.raise_for_status()
        except NoResultFound:
            log_msg = (
                f"Run with contest_id={contest_id}, run_id={run_id} "
                f"doesn't exist, task requeued"
            )
            current_app.logger.exception(log_msg)
        except RequestException:
            log_msg = 'Ejudge-front bad response or timeout, task requeued'
            current_app.logger.exception(log_msg)
        else:
            log_msg = f'Run with contest_id={contest_id}, run_id={run_id} sended'
            current_app.logger.info(log_msg)
            return
        q = rq.get_queue()
        q.enqueue(send_run, contest_id, run_id, json)


def form_json(contest_id: int, run_id: int) -> dict:
    run = load_run(contest_id, run_id)
    protocol_id = put_protocol_to_mongo(run)
    data = run_schema.dump(run).data
    data['protocol_id'] = protocol_id
    return data


def load_run(contest_id: int, run_id: int) -> EjudgeRun:
    """
    :return: EjudgeRun or throw NoResultFound.
    """
    run = (
        db.session.query(EjudgeRun)
        .filter_by(contest_id=contest_id)
        .filter_by(run_id=run_id)
        .one()
    )
    return run


def put_protocol_to_mongo(run: EjudgeRun) -> str:
    """
    :return: hex encoded version of ObjectId.
    """
    protocol = get_full_protocol(run)
    protocol_id = mongo.db.protocol.insert_one(protocol).inserted_id
    return str(protocol_id)
