import unittest
from unittest.mock import MagicMock, patch

from requests import HTTPError

from ejudge_listener.exceptions import ProtocolNotFoundError
from ejudge_listener.requests import EjudgeRequest
from ejudge_listener.tasks import process_run, send_non_terminal, send_terminal
from ejudge_listener.utils import make_log_message
from tests.unit.base import TestCase

MONGO_PROTOCOL_ID = '507f1f77bcf86cd799439011'

PROCESS_RUN_10_1_JSON = {
    'run_id': 10,
    'contest_id': 1,
    'mongo_protocol_id': MONGO_PROTOCOL_ID,
    'status': None,
    'lang_id': None,
    'score': None,
    'last_change_time': None,
    'create_time': None,
    'run_uuid': None,
    'test_num': None,
}

TERMINAL_STATUS = 0
NON_TERMINAL_STATUS = 96

EJUDGE_REQUEST_WITH_EXISTING_RUN = EjudgeRequest(10, 1, 0)
EJUDGE_REQUEST_WITH_NON_EXISTING_RUN = EjudgeRequest(7777, 5555, 0)


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

    @patch(
        'ejudge_listener.tasks.insert_protocol_to_mongo', return_value=MONGO_PROTOCOL_ID
    )
    @patch(
        'ejudge_listener.tasks.read_protocol',
        return_value={'protocol': 'nice_protocol'},
    )
    def test_db_contain_run_and_ejudge_contain_protocol(
        self, mock_get_full_protocol, mock_insert_protocol_to_mongo
    ):
        self.assertEqual(
            process_run(EJUDGE_REQUEST_WITH_EXISTING_RUN), PROCESS_RUN_10_1_JSON
        )
        mock_insert_protocol_to_mongo.assert_called()

    @patch(
        'ejudge_listener.tasks.insert_protocol_to_mongo', return_value=MONGO_PROTOCOL_ID
    )
    @patch('ejudge_listener.tasks.read_protocol', side_effect=ProtocolNotFoundError)
    def test_db_contain_run_but_ejudge_doesnt_have_protocol(
        self, mock_get_full_protocol, mock_insert_protocol_to_mongo
    ):
        with self.assertRaises(ProtocolNotFoundError):
            process_run(EJUDGE_REQUEST_WITH_EXISTING_RUN)
        mock_insert_protocol_to_mongo.assert_not_called()


@patch('requests.post')
class TestSendJson(TestCase):
    SUCCESS_LOG_MSG = make_log_message(
        'send_non_terminal', 'success', EJUDGE_REQUEST_WITH_EXISTING_RUN
    )

    REVOKED_LOG_MSG = make_log_message(
        'send_non_terminal', 'revoked', EJUDGE_REQUEST_WITH_EXISTING_RUN
    )

    def setUp(self):
        super().setUp()
        self.create_runs()
        self.addCleanup(patch.stopall)

    # -------------------------------------------------------------------------

    @patch('logging.info')
    def test_nonterminal_to_working_front(self, mock_logger, mock_response):
        success_log_msg = make_log_message(
            'send_non_terminal', 'success', EJUDGE_REQUEST_WITH_EXISTING_RUN
        )
        send_non_terminal(EJUDGE_REQUEST_WITH_EXISTING_RUN)
        mock_logger.assert_called_once_with(success_log_msg)

    @patch('logging.exception')
    def test_nonterminal_to_not_working_front(self, mock_logger, mock_response):
        revoked_log_msg = make_log_message(
            'send_non_terminal', 'revoked', EJUDGE_REQUEST_WITH_EXISTING_RUN
        )
        mock_response.return_value.raise_for_status = MagicMock(side_effect=HTTPError())
        send_non_terminal(EJUDGE_REQUEST_WITH_EXISTING_RUN)
        mock_logger.assert_called_once_with(revoked_log_msg)

    @patch('logging.info')
    def test_terminal_to_working_front(self, mock_logger, mock_response):
        success_log_msg = make_log_message(
            'send_terminal', 'success', EJUDGE_REQUEST_WITH_EXISTING_RUN
        )
        run_json = PROCESS_RUN_10_1_JSON
        run_json['status'] = TERMINAL_STATUS
        send_terminal(EJUDGE_REQUEST_WITH_EXISTING_RUN, run_json)
        mock_logger.assert_called_once_with(success_log_msg)

    @unittest.skip('Not ready yet')
    @patch('ejudge_listener.tasks.mongo_rollback')
    def test_terminal_to_not_working_front_400_error(
        self, patch_mongo_rollback, mock_response
    ):
        run_json = PROCESS_RUN_10_1_JSON
        run_json['status'] = TERMINAL_STATUS
        error = MagicMock(side_effect=HTTPError())
        error.status_code.return_value = 400
        mock_response.return_value.raise_for_status = error
        send_terminal(EJUDGE_REQUEST_WITH_EXISTING_RUN, run_json)
        patch_mongo_rollback.assert_called_once_with(run_json)
