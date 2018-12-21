import functools

import requests
from flask import current_app
from requests import HTTPError

from app import db, create_app
from app.models import EjudgeRun
from app.schemas import EjudgeRunSchema


def task(func):
    """
    This function is going to run in a separate process that is controlled by RQ,
    not Flask, so if any unexpected errors occur the task will abort, RQ will display
    the error to the console and then will go back to wait for new jobs. So basically,
    unless you are watching the output of the RQ worker or logging it to a file, you
    will never find out there was an error.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        app = create_app()
        app.app_context().push()
        try:
            return func(*args, **kwargs)
        except:
            app.logger.exception('Unhandled exception')

    return wrapper


@task
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

    run_schema = EjudgeRunSchema()
    json = run_schema.dump(run).data
    return json
