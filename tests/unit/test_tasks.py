from unittest.mock import patch, MagicMock

from requests import HTTPError

from ejudge_listener.exceptions import ProtocolNotFoundError
from ejudge_listener.tasks import process_run, send_json_to_front, send_to_ejudge_front
from tests.unit.base import TestCase

MONGO_PROTOCOL_ID = '507f1f77bcf86cd799439011'

process_run_10_1_json = {
    'run_id': 10,
    'contest_id': 1,
    'mongo_protocol_id': MONGO_PROTOCOL_ID,
    'status': None,
    'lang_id': None,
    'score': None,
    'last_change_time': None,
    'create_time': None,
    'run_uuid': None,
    'test_num': None
}

TERMINAL_STATUS = 0
NON_TERMINAL_STATUS = 96

LOG_MSG = 'Run with run_id=10 contest_id=1 sended successfully'
ERROR_LOG_MSG = 'Ejudge-front bad response or timeout, task requeued'


class TestProcessRun(TestCase):
    def setUp(self):
        super().setUp()
        self.create_runs()
        self.addCleanup(patch.stopall)

    # -------------------------------------------------------------------------

    # noinspection PyUnresolvedReferences,PyTypeChecker
    def test_db_doesnt_contain_run(self):
        with self.assertRaises(SystemExit) as cm:
            process_run(7777, 5555)
        self.assertEqual(cm.exception.code, 0)

    @patch('ejudge_listener.tasks.insert_protocol_to_mongo')
    @patch('ejudge_listener.tasks.get_full_protocol')
    def test_db_contain_run_and_ejudge_contain_protocol(
            self,
            mock_get_full_protocol,
            mock_insert_protocol_to_mongo,

    ):
        mock_get_full_protocol.return_value = {'protocol': 'nice protocol'}
        mock_insert_protocol_to_mongo.return_value = MONGO_PROTOCOL_ID

        self.assertEqual(process_run(10, 1), process_run_10_1_json)
        mock_insert_protocol_to_mongo.assert_called()

    @patch('ejudge_listener.tasks.insert_protocol_to_mongo')
    @patch('ejudge_listener.tasks.get_full_protocol', side_effect=ProtocolNotFoundError)
    def test_db_contain_run_but_ejudge_doesnt_have_protocol(
            self,
            mock_get_full_protocol,
            mock_insert_protocol_to_mongo
    ):
        mock_get_full_protocol.return_value = None
        mock_insert_protocol_to_mongo.return_value = MONGO_PROTOCOL_ID

        with self.assertRaises(ProtocolNotFoundError):
            process_run(10, 1)
        mock_insert_protocol_to_mongo.assert_not_called()


@patch('rq.queue.Queue.enqueue')
@patch('requests.post')
class TestSendJson(TestCase):
    def setUp(self):
        super().setUp()
        self.create_runs()
        self.addCleanup(patch.stopall)

    # -------------------------------------------------------------------------

    @patch('ejudge_listener.tasks.current_app.logger.info')
    def test_send_json_to_working_front(
            self,
            mock_app_logger,
            mock_response,
            mock_enqueue
    ):
        run_json = process_run_10_1_json
        send_json_to_front(10, 1, run_json)
        mock_app_logger.assert_called_once_with(LOG_MSG)
        mock_enqueue.assert_not_called()

    @patch('ejudge_listener.tasks.current_app.logger.exception')
    def test_send_json_to_not_working_front_with_terminal_status(
            self,
            mock_app_logger,
            mock_response,
            mock_enqueue
    ):
        run_json = process_run_10_1_json
        run_json['status'] = TERMINAL_STATUS

        mock_response.return_value.raise_for_status = MagicMock(side_effect=HTTPError())

        send_json_to_front(10, 1, run_json)
        mock_app_logger.assert_called_once_with(ERROR_LOG_MSG)
        mock_enqueue.assert_called_once_with(send_to_ejudge_front, 1, 10, run_json)

    @patch('ejudge_listener.tasks.current_app.logger.exception')
    def test_send_json_to_not_working_front_with_not_terminal_status(
            self,
            mock_app_logger,
            mock_response,
            mock_enqueue
    ):
        run_json = process_run_10_1_json
        run_json['status'] = NON_TERMINAL_STATUS

        mock_response.return_value.raise_for_status = MagicMock(side_effect=HTTPError())

        send_json_to_front(10, 1, run_json)
        mock_app_logger.assert_called_once_with(ERROR_LOG_MSG)
        mock_enqueue.assert_not_called()
