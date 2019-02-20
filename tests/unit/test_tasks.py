from unittest.mock import MagicMock, patch

from requests import HTTPError, RequestException

from ejudge_listener.exceptions import ProtocolNotFoundError
from ejudge_listener.requests import EjudgeRequest
from ejudge_listener.tasks import (
    process_run,
    send_json_to_front,
)
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

LOG_MSG = 'Run with run_id=10 contest_id=1 sent successfully'
ERROR_LOG_MSG = 'Ejudge-front bad response or timeout'

EJUDGE_REQUEST_WITH_NON_EXISTING_RUN = EjudgeRequest(7777, 5555, 0)
EJUDGE_REQUEST_WITH_EXISTING_RUN = EjudgeRequest(10, 1, 0)


class TestProcessRun(TestCase):
    def setUp(self):
        super().setUp()
        self.create_runs()
        self.addCleanup(patch.stopall)

    # -------------------------------------------------------------------------

    # noinspection PyUnresolvedReferences,PyTypeChecker
    def test_db_doesnt_contain_run(self):
        with self.assertRaises(SystemExit) as cm:
            process_run(EJUDGE_REQUEST_WITH_NON_EXISTING_RUN)
        self.assertEqual(cm.exception.code, 0)

    @patch('ejudge_listener.tasks.insert_protocol_to_mongo', return_value=MONGO_PROTOCOL_ID)
    @patch('ejudge_listener.tasks.read_protocol', return_value={'protocol': 'nice_protocol'})
    def test_db_contain_run_and_ejudge_contain_protocol(
            self,
            mock_get_full_protocol,
            mock_insert_protocol_to_mongo,

    ):
        self.assertEqual(process_run(EJUDGE_REQUEST_WITH_EXISTING_RUN), process_run_10_1_json)
        mock_insert_protocol_to_mongo.assert_called()

    @patch('ejudge_listener.tasks.insert_protocol_to_mongo', return_value=MONGO_PROTOCOL_ID)
    @patch('ejudge_listener.tasks.read_protocol', side_effect=ProtocolNotFoundError)
    def test_db_contain_run_but_ejudge_doesnt_have_protocol(
            self,
            mock_get_full_protocol,
            mock_insert_protocol_to_mongo
    ):
        with self.assertRaises(ProtocolNotFoundError):
            process_run(EJUDGE_REQUEST_WITH_EXISTING_RUN)
        mock_insert_protocol_to_mongo.assert_not_called()


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
            mock_response
    ):
        run_json = process_run_10_1_json
        send_json_to_front(run_json)
        mock_app_logger.assert_called_once_with(LOG_MSG)

    @patch('ejudge_listener.tasks.current_app.logger.exception')
    def test_send_json_to_not_working_front(
            self,
            mock_app_logger,
            mock_response,
    ):
        run_json = process_run_10_1_json
        run_json['status'] = TERMINAL_STATUS

        mock_response.return_value.raise_for_status = MagicMock(side_effect=HTTPError())
        with self.assertRaises(RequestException):
            send_json_to_front(run_json)
        mock_app_logger.assert_called_once_with(ERROR_LOG_MSG)
