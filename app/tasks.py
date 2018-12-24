import requests
from flask import current_app
from requests import HTTPError

from app.db import db
from app.models import EjudgeRun
from app.plugins import rq
from app.schemas import EjudgeRunSchema

run_schema = EjudgeRunSchema()


@rq.job # todo test :)
def send_run(contest_id, run_id, json=None):
    content = json or load_run(contest_id, run_id)
    r = requests.post('ejudge-front', json=content)  # todo url for ejudge-front
    try:
        r.raise_for_status()
    except HTTPError:
        current_app.task_queue.enqueue(send_run, contest_id, run_id, content)


def load_run(contest_id, run_id):
    try:
        run = (
            db.session.query(EjudgeRun)
            .filter_by(contest_id=contest_id)
            .filter_by(run_id=run_id)
            .one()
        )
    except Exception as e:
        print(e)  # todo catch error

    return run_schema.dump(run).data
