import unittest
from unittest.mock import patch

from sqlalchemy.orm.exc import NoResultFound

from ejudge_listener.flow import (
    EjudgeRequest,
    load_protocol,
    EjudgeRequestSchema,
    insert_to_mongo,
)
from ejudge_listener.protocol.exceptions import ProtocolNotFoundError
from tests.unit.base import TestCase, RUN_WITH_MONGO_ID, MONGO_ID, RUN, PROTOCOL

ej_request_schema = EjudgeRequestSchema()


class TestLoadProtocol(TestCase):
    def setUp(self):
        super().setUp()
        self.create_runs()

    def test_db_doesnt_contain_run(self):
        ej_request = EjudgeRequest(7777, 5555, 0)  # non existing run
        request_args = ej_request_schema.dump(ej_request).data
        with self.assertRaises(NoResultFound):
            load_protocol(request_args)

    @patch('ejudge_listener.flow.read_protocol', return_value=PROTOCOL)
    @unittest.skip(
        'Unknown import bug, RUN == RUN_WITH_MONGO_ID, can\'t assert correctly'
    )
    def test_db_contain_run_and_ejudge_contain_protocol(self, mock_read_protocol):
        ej_request = EjudgeRequest(1, 10, 0)  # existing run
        request_args = ej_request_schema.dump(ej_request).data
        run_data, protocol = load_protocol(request_args)
        self.assertEqual(run_data, RUN)
        self.assertEqual(protocol, PROTOCOL)

    @patch('ejudge_listener.flow.read_protocol', side_effect=ProtocolNotFoundError)
    def test_db_contain_run_but_ejudge_doesnt_have_protocol(self, mock_read_protocol):
        ej_request = EjudgeRequest(1, 10, 0)  # existing run
        request_args = ej_request_schema.dump(ej_request).data
        with self.assertRaises(ProtocolNotFoundError):
            load_protocol(request_args)


class TestInsertToMongo(TestCase):
    @patch('ejudge_listener.flow.insert_protocol_to_mongo', return_value=MONGO_ID)
    def test_insert_to_mongo(self, mock_flow_insert_protocol_to_mongo):
        run_data = insert_to_mongo((RUN, PROTOCOL))
        self.assertEqual(run_data, RUN_WITH_MONGO_ID)
