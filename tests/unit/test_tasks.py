import unittest
from unittest.mock import patch, Mock

from celery.exceptions import Retry
from requests import HTTPError, Timeout
from sqlalchemy.orm.exc import NoResultFound

from ejudge_listener.protocol.exceptions import ProtocolNotFoundError, TestsNotFoundError
from ejudge_listener.tasks import send_non_terminal, load_protocol, send_terminal
from tests.unit.base import TestCase, REQUEST_ARGS, PROTOCOL, RUN_WITH_MONGO_ID


class TestSendNonTerminal(TestCase):
    @patch('requests.post')
    def test_send_non_terminal_with_working_front(self, mock_post):
        send_non_terminal(REQUEST_ARGS)
        mock_post.assert_called_once()


@patch('ejudge_listener.tasks.load_protocol.retry', side_effect=Retry)
class TestLoadProtocol(TestCase):
    @patch('ejudge_listener.flow.load_protocol', return_value=PROTOCOL)
    def test_protocol_exist(self, mock_flow_load_protocol, mock_retry):
        self.assertEqual(load_protocol(REQUEST_ARGS), PROTOCOL)
        mock_retry.assert_not_called()

    @patch('ejudge_listener.flow.load_protocol', side_effect=NoResultFound)
    def test_run_not_exist(self, mock_flow_load_protocol, mock_retry):
        load_protocol(REQUEST_ARGS)
        self.assertIsNone(load_protocol.request.chain)
        mock_retry.assert_not_called()

    @patch('ejudge_listener.flow.load_protocol', side_effect=ProtocolNotFoundError)
    def test_protocol_not_exist(self, mock_flow_load_protocol, mock_retry):
        with self.assertRaises(Retry):
            load_protocol(REQUEST_ARGS)
        mock_retry.assert_called_once()

    @patch('ejudge_listener.flow.load_protocol', side_effect=TestsNotFoundError)
    def test_protocol_tests_not_exist(self, mock_flow_load_protocol, mock_retry):
        with self.assertRaises(Retry):
            load_protocol(REQUEST_ARGS)
        mock_retry.assert_called_once()



@patch('ejudge_listener.tasks.send_terminal.retry', side_effect=Retry)
@patch('ejudge_listener.tasks.mongo_rollback')
class TestSendTerminal(TestCase):
    @patch('requests.post')
    def test_ok_response_from_ejudge_front(
        self, mock_post, mock_mongo_rollback, mock_retry
    ):
        send_terminal(RUN_WITH_MONGO_ID)
        mock_mongo_rollback.assert_not_called()
        mock_retry.assert_not_called()

    @patch('requests.post', side_effect=HTTPError(response=Mock(status_code=400)))
    def test_4xx_response_from_ejudge_front(
        self, mock_post, mock_mongo_rollback, mock_retry
    ):
        send_terminal(RUN_WITH_MONGO_ID)
        mock_mongo_rollback.assert_called_once_with(RUN_WITH_MONGO_ID)
        mock_retry.assert_not_called()

    @patch('requests.post', side_effect=HTTPError(response=Mock(status_code=500)))
    def test_5xx_response_from_ejudge_front(
        self, mock_post, mock_mongo_rollback, mock_retry
    ):
        with self.assertRaises(Retry):
            send_terminal(RUN_WITH_MONGO_ID)
        mock_mongo_rollback.assert_not_called()
        mock_retry.assert_called_once()

    @patch('requests.post', side_effect=Timeout)
    def test_timeout_error(self, mock_post, mock_mongo_rollback, mock_retry):
        with self.assertRaises(Retry):
            send_terminal(RUN_WITH_MONGO_ID)
        mock_mongo_rollback.assert_not_called()
        mock_retry.assert_called_once()
