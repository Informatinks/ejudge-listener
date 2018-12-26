import requests
import uuid

from bson import ObjectId
from flask import current_app
from requests import RequestException
from sqlalchemy.orm.exc import NoResultFound

from app import create_app
from app.models import EjudgeRun
from app.models import db
from app.plugins import rq, mongo
from app.protocol.protocol import get_full_protocol
from app.schemas import EjudgeRunSchema

run_schema = EjudgeRunSchema()


def send_run(contest_id, run_id, json=None):
    app = create_app()
    with app.app_context():
        try:
            content = json or load_run(contest_id, run_id)
            r = requests.post('ejudge-front', json=content, timeout=3)
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


def load_run(contest_id: int, run_id: int) -> dict:
    run = (
        db.session.query(EjudgeRun)
        .filter_by(contest_id=contest_id)
        .filter_by(run_id=run_id)
        .one()
    )
    data = run_schema.dump(run).data
    protocol_id = put_protocol_to_mongo(run)
    data['protocol_id'] = protocol_id.binary
    return data


def put_protocol_to_mongo(run):
    protocol = get_full_protocol(run)  # TODO: refactoring
    random_id = uuid.uuid4().hex
    protocol_id: ObjectId = mongo.db.protocol.insert_one(protocol).inserted_id

    return protocol_id
