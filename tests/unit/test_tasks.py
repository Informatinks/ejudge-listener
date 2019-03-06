from ejudge_listener.flow import EjudgeRequest
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
    'test_num': None,
}

TERMINAL_STATUS = 0
NON_TERMINAL_STATUS = 96

LOG_MSG = 'Run with run_id=10 contest_id=1 sent successfully'
ERROR_LOG_MSG = 'Ejudge-front bad response or timeout'

EJUDGE_REQUEST_WITH_NON_EXISTING_RUN = EjudgeRequest(7777, 5555, 0)
EJUDGE_REQUEST_WITH_EXISTING_RUN = EjudgeRequest(10, 1, 0)


# NON TERMINAL
# -----------------------------------------------------------------------------
class TestSendNonTerminal(TestCase):
    ...


# TERMINAL
# -----------------------------------------------------------------------------
class TestLoadProtocol(TestCase):
    ...


class TestInsertToMongo(TestCase):
    ...


class TestSendTerminal(TestCase):
    ...
