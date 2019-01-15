from unittest.mock import patch
from ejudge_listener.models.ejudge_run import db, EjudgeRun
from ejudge_listener.tasks import process_run
from tests.unit.base import TestCase

MONGO_PROTOCOL_ID = 1239


class Tasks(TestCase):
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
