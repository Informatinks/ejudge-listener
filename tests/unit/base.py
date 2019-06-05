import copy

import flask_testing

from ejudge_listener import create_app
from ejudge_listener.extensions import db
from ejudge_listener.models import EjudgeRun
from unittest.mock import patch

REQUEST_ARGS = {'contest_id': 1, 'run_id': 10, 'status': 0}
MONGO_ID = '507f1f77bcf86cd799439011'
RUN = {
    'run_id': 10,
    'contest_id': 1,
    'status': None,
    'lang_id': None,
    'score': None,
    'last_change_time': None,
    'create_time': None,
    'run_uuid': None,
    'test_num': None,
}
RUN_WITH_MONGO_ID = {
    'run_id': 10,
    'contest_id': 1,
    'status': None,
    'lang_id': None,
    'score': None,
    'last_change_time': None,
    'create_time': None,
    'run_uuid': None,
    'test_num': None,
    'mongo_protocol_id': MONGO_ID,
}
PROTOCOL = {'tests': 'nice_tests', 'audit': 'nice_audit'}


class TestCase(flask_testing.TestCase):
    def create_app(self):
        app = create_app('ejudge_listener.config.TestConfig')
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
        self.run_data = copy.deepcopy(RUN)
        self.addCleanup(patch.stopall)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
