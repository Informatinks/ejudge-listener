from unittest.mock import patch, MagicMock

from requests import HTTPError

from ejudge_listener.tasks import process_run, send_json_to_front, send_run
from tests.unit.base import TestCase

MONGO_PROTOCOL_ID = '507f1f77bcf86cd799439011'

process_run_1_10_json = {
    'contest_id': 1,
    'run_id': 10,
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

LOG_MSG = 'Run with contest_id=1, run_id=10 sended successfully'
ERROR_LOG_MSG = 'Ejudge-front bad response or timeout, task requeued'


class Tasks(TestCase):
    def setUp(self):
        super().setUp()
        self.create_runs()

    @patch('ejudge_listener.tasks.put_protocol_to_mongo')
    def test_process_run_with_existent_run(self, mock_put_protocol_to_mongo):
        mock_put_protocol_to_mongo.return_value = MONGO_PROTOCOL_ID

        self.assertEqual(process_run(1, 10), process_run_1_10_json)

        mock_put_protocol_to_mongo.assert_called()

    @patch('ejudge_listener.tasks.put_protocol_to_mongo')
    def test_process_run_with_not_existent_run(self, mock_put_protocol_to_mongo):
        mock_put_protocol_to_mongo.return_value = MONGO_PROTOCOL_ID

        with self.assertRaises(SystemExit) as cm:
            process_run(5555, 7777)

        print(cm.exception.code)
        self.assertEqual(cm.exception.code, 0)

    @patch('ejudge_listener.tasks.current_app.logger.info')
    @patch('rq.queue.Queue.enqueue')
    @patch('requests.post')
    def test_send_json_to_working_front(
            self,
            mock_response,
            mock_enqueue,
            mock_app_logger
    ):
        run_json = process_run_1_10_json
        send_json_to_front(1, 10, run_json)
        mock_app_logger.assert_called_once_with(LOG_MSG)
        mock_enqueue.assert_not_called()

    @patch('ejudge_listener.tasks.current_app.logger.exception')
    @patch('rq.queue.Queue.enqueue')
    @patch('requests.post')
    def test_send_json_to_not_working_front_with_terminal_status(
            self,
            mock_response,
            mock_enqueue,
            mock_app_logger
    ):
        run_json = process_run_1_10_json
        run_json['status'] = TERMINAL_STATUS

        mock_response.return_value.raise_for_status = MagicMock(side_effect=HTTPError())

        send_json_to_front(1, 10, run_json)
        mock_app_logger.assert_called_once_with(ERROR_LOG_MSG)
        mock_enqueue.assert_called_once_with(send_run, 1, 10, run_json)

    @patch('ejudge_listener.tasks.current_app.logger.exception')
    @patch('rq.queue.Queue.enqueue')
    @patch('requests.post')
    def test_send_json_to_not_working_front_with_not_terminal_status(
            self,
            mock_response,
            mock_enqueue,
            mock_app_logger
    ):
        run_json = process_run_1_10_json
        run_json['status'] = NON_TERMINAL_STATUS

        mock_response.return_value.raise_for_status = MagicMock(side_effect=HTTPError())

        send_json_to_front(1, 10, run_json)
        mock_app_logger.assert_called_once_with(ERROR_LOG_MSG)
        mock_enqueue.assert_not_called()
