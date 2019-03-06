from unittest.mock import patch

from requests import HTTPError
from sqlalchemy.orm.exc import NoResultFound

from ejudge_listener.flow import (
    EjudgeRequest,
    send_non_terminal,
    load_protocol,
    EjudgeRequestSchema,
    EjudgeRunSchema,
)
from ejudge_listener.protocol.exceptions import ProtocolNotFoundError
from tests.unit.base import TestCase

MONGO_ID = '507f1f77bcf86cd799439011'


PROCESS_RUN_10_1_JSON = {
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

TERMINAL_STATUS = 0
NON_TERMINAL_STATUS = 96

LOG_MSG = 'Run with run_id=10 contest_id=1 sent successfully'
ERROR_LOG_MSG = 'Ejudge-front bad response or timeout'

ej_request_schema = EjudgeRequestSchema()
ej_run_schema = EjudgeRunSchema()


EJUDGE_REQUEST_WITH_EXISTING_RUN = EjudgeRequest(10, 1, 0)


# NON TERMINAL
# -----------------------------------------------------------------------------
class TestSendNonTerminal(TestCase):
    non_terminal_json = {'contest_id': 1, 'run_id': 2, 'status': 98}

    def setUp(self):
        super().setUp()

    # -------------------------------------------------------------------------
    @patch('requests.post')
    def test_send_non_terminal_with_working_front(self, mock_post):
        send_non_terminal(self.non_terminal_json)

    @patch('requests.post', side_effect=HTTPError('Front is dead'))
    def test_send_non_terminal_with_not_working_front(self, mock_post):
        with self.assertRaises(HTTPError):
            send_non_terminal(self.non_terminal_json)


# TERMINAL
# -----------------------------------------------------------------------------
class TestLoadProtocol(TestCase):
    ej_request_schema = EjudgeRequestSchema()
    protocol = {'tests': 'nice_tests', 'audit': 'nice_audit'}

    def setUp(self):
        super().setUp()
        self.create_runs()

    # -------------------------------------------------------------------------

    def test_db_doesnt_contain_run(self):
        ej_request = EjudgeRequest(7777, 5555, 0)  # non existing run
        request_args = ej_request_schema.dump(ej_request).data
        with self.assertRaises(NoResultFound):
            load_protocol(request_args)

    @patch('ejudge_listener.flow.read_protocol', return_value=protocol)
    def test_db_contain_run_and_ejudge_contain_protocol(self, mock_read_protocol):
        ej_request = EjudgeRequest(1, 10, 0)  # existing run
        request_args = ej_request_schema.dump(ej_request).data
        run_data, protocol = load_protocol(request_args)
        self.assertEqual(run_data, PROCESS_RUN_10_1_JSON)
        self.assertEqual(protocol, self.protocol)

    @patch('ejudge_listener.flow.read_protocol', side_effect=ProtocolNotFoundError)
    def test_db_contain_run_but_ejudge_doesnt_have_protocol(self, mock_read_protocol):
        ej_request = EjudgeRequest(1, 10, 0)  # existing run
        request_args = ej_request_schema.dump(ej_request).data
        with self.assertRaises(ProtocolNotFoundError):
            load_protocol(request_args)


class TestInsertToMongo(TestCase):
    ...


class TestSendTerminal(TestCase):
    ...
