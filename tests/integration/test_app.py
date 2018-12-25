import unittest
import time

from flask import url_for
from flask_testing import TestCase

from app import create_app, db
from app.models import EjudgeRun
from config import TestConfig


class AppTest(TestCase):
    valid_int_request = {'contest_id': 1, 'run_id': 10}

    def create_app(self):
        app = create_app(TestConfig)
        return app

    def setUp(self):
        db.create_all()
        for i in range(1, 11):
            run = EjudgeRun(contest_id=i, run_id=i * 10)
            db.session.add(run)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def send_request(self, params):
        return self.client.get(url_for('update_run', **params))

    # ------------------------------------------------------------------------

    def test_db_created(self):
        runs = db.session.query(EjudgeRun).all()
        self.assertEqual(10, len(runs))

    @unittest.skip(
        "Can't test with sqlite memory, when multiprocessing, need mock for db"
    )
    def test_app(self):
        self.send_request(self.valid_int_request)


if __name__ == '__main__':
    unittest.main()
