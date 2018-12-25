import requests
from flask import current_app
from requests import RequestException
from sqlalchemy.orm.exc import NoResultFound

from app import create_app
from app.models import db, EjudgeRun
from app.schemas import EjudgeRunSchema
from app.plugins import rq

run_schema = EjudgeRunSchema()


def send_run(contest_id, run_id, json=None):
    app = create_app()
    with app.app_context():
        try:
            content = json or load_run(contest_id, run_id)
            r = requests.post('ejudge-front', json=content, timeout=3)
            r.raise_for_status()
        except NoResultFound:
            current_app.logger.exception(
                f"Run with contest_id={contest_id}, run_id={run_id} "
                f"doesn't exist, task requeued"
            )
        except RequestException:
            current_app.logger.exception(
                'Ejudge-front bad response or timeout, task requeued'
            )
        else:
            current_app.logger.info(
                f'Run with contest_id={contest_id}, run_id={run_id} sended'
            )
            return
        q = rq.get_queue()
        q.enqueue(send_run, contest_id, run_id, json)


def load_run(contest_id, run_id):
    run = (
        db.session.query(EjudgeRun)
        .filter_by(contest_id=contest_id)
        .filter_by(run_id=run_id)
        .one()
    )
    return run_schema.dump(run).data
