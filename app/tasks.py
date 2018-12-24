import requests

from app import create_app
from app.models import db, EjudgeRun
from app.schemas import EjudgeRunSchema
from app.plugins import rq


run_schema = EjudgeRunSchema()


def send_run(contest_id, run_id, json=None):
    app = create_app()
    with app.app_context():
        content = json or load_run(contest_id, run_id)
        r = requests.post('ejudge-front', json=content)  # todo url for ejudge-front
        if not r:
            q = rq.get_queue()
            q.enqueue(send_run, contest_id, run_id, content)


def load_run(contest_id, run_id):
    run = (
        db.session.query(EjudgeRun)
        .filter_by(contest_id=contest_id)
        .filter_by(run_id=run_id)
        .one()
    )  # todo catch exception

    return run_schema.dump(run).data
