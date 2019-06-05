import random
from unittest.mock import patch
from flask import url_for
from tests.unit.base import TestCase

MIN_ID = 1
MAX_ID = 1_000_000


def random_id():
    return random.randint(MIN_ID, MAX_ID)


class TestView(TestCase):
    valid_terminal_int_request = {
        'contest_id': random_id(),
        'run_id': random_id(),
        'new_status': 0,
    }

    valid_terminal_str_request = {
        'contest_id': str(random_id()),
        'run_id': str(random_id()),
        'new_status': 0,
    }

    valid_non_terminal_int_request = {
        'contest_id': random_id(),
        'run_id': random_id(),
        'new_status': 98,
    }

    valid_non_terminal_str_request = {
        'contest_id': str(random_id()),
        'run_id': str(random_id()),
        'new_status': 98,
    }

    def send_request(self, params):
        return self.client.get(url_for('update_run', **params))

    # -------------------------------------------------------------------------

    @patch('ejudge_listener.views.make_terminal_chain')
    def test_terminal(self, mock_terminal_delay):
        self.assert200(self.send_request(self.valid_terminal_int_request))
        self.assert200(self.send_request(self.valid_terminal_str_request))
        self.assertEqual(mock_terminal_delay.call_count, 2)

    @patch('ejudge_listener.views.make_non_terminal_chain')
    def test_non_terminal(self, mock_non_terminal_delay):
        self.assert200(self.send_request(self.valid_non_terminal_int_request))
        self.assert200(self.send_request(self.valid_non_terminal_str_request))
        self.assertEqual(mock_non_terminal_delay.call_count, 2)
