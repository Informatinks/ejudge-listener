import flask_testing

from ejudge_listener import create_app
from ejudge_listener.models import db
from ejudge_listener.models.ejudge_run import EjudgeRun


class TestCase(flask_testing.TestCase):
    def create_app(self):
        app = create_app()
        return app

    def create_runs(self):
        """
        run_id | contest_id
          10   |     1
          20   |     2
          30   |     3
          40   |     4
          50   |     5
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
