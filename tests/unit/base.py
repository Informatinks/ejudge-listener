import flask_testing

from ejudge_listener import create_app
from ejudge_listener.extensions import db
from ejudge_listener.models import EjudgeRun
from unittest.mock import patch


class TestCase(flask_testing.TestCase):
    def create_app(self):
        app = create_app()
        return app

    def create_runs(self):
        """
        contest_id | run_id
            1      |   10
            2      |   20
            3      |   30
            4      |   40
            5      |   50
        """
        for i in range(1, 6):
            run = EjudgeRun(contest_id=i, run_id=i * 10)
            db.session.add(run)
        db.session.commit()

    def setUp(self):
        db.drop_all()
        db.create_all()
        self.addCleanup(patch.stopall)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
