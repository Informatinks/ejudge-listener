import unittest

import flask_testing

from ejudge_listener import create_app
from ejudge_listener.models import db
from ejudge_listener.models.ejudge_run import EjudgeRun
from ejudge_listener.models.problem import EjudgeProblem


class TestCase(flask_testing.TestCase):
    def create_app(self):
        app = create_app(is_test=True)
        return app

    def create_runs(self):
        """
        contest_id | run_id
             1     |    10
             2     |    20
             3     |    30
             4     |    40
             5     |    50
        """
        for i in range(1, 6):
            run = EjudgeRun(contest_id=i, run_id=i * 10)
            db.session.add(run)
        db.session.commit()

    def setUp(self):
        db.drop_all()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
