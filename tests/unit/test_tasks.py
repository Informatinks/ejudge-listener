from unittest.mock import patch, MagicMock

from flask_testing import TestCase

from ejudge_listener import create_app
from config import TestConfig
from ejudge_listener.models.ejudge_run import db, EjudgeRun
from ejudge_listener.tasks import process_run

MONGO_PROTOCOL_ID = 1239


class Tasks(TestCase):
    def create_app(self):
        app = create_app(TestConfig)
        return app

    def init_db(self):
        """
        contest_id | run_id
             1     |    10
             2     |    20
             3     |    30
             4     |    40
             5     |    50
        """
        for i in range(1, 6):
            run = EjudgeRun(contest_id=1, run_id=10)
            db.session.add(run)
        db.session.commit()

    def setUp(self):
        db.drop_all()
        db.create_all()
        self.init_db()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    @patch('ejudge_listener.tasks.put_protocol_to_mongo')
    @patch('sys.exit')
    def test_process_run(self, mock_sysexit, mock_put_protocol_to_mongo):
        mock_put_protocol_to_mongo.return_value = MONGO_PROTOCOL_ID

        run = EjudgeRun(contest_id=1, run_id=10)
        db.session.add(run)
        db.session.commit()

        process_run(1, 10)

        mock_sysexit.assert_not_called()

    @patch('ejudge_listener.tasks.put_protocol_to_mongo')
    @patch('sys.exit')
    def test_process_run_failed(self, mock_sysexit, mock_put_protocol_to_mongo):
        mock_put_protocol_to_mongo.return_value = MONGO_PROTOCOL_ID

        run = EjudgeRun(contest_id=1, run_id=10)
        db.session.add(run)
        db.session.commit()

        process_run(5555, 7777)

        mock_sysexit.assert_called_once_with(0)
