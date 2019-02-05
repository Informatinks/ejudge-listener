import random
from unittest.mock import patch

from flask import url_for

from tests.unit.base import TestCase

MIN_ID = 1
MAX_ID = 1_000_000


def random_id():
    return random.randint(MIN_ID, MAX_ID)


@patch('rq.queue.Queue.enqueue')
class TestView(TestCase):
    valid_int_request = {'contest_id': random_id(), 'run_id': random_id()}

    valid_str_request = {'contest_id': str(random_id()), 'run_id': str(random_id())}

    invalid_ids = ['', 'one', 'dog', True, False, None]  # All possible
    invalid_requests = [{'contest_id': i_id, 'run_id': i_id} for i_id in invalid_ids]

    def assert422(self, response, message=None):
        self.assertStatus(response, 422, message)

    def send_request(self, params):
        return self.client.get(url_for('update_run', **params))

    def send_6_invalid_requests(self):
        return [self.send_request(request) for request in self.invalid_requests]

    # -------------------------------------------------------------------------

    def test_valid_request(self, mock_enqueue):
        self.assert200(self.send_request(self.valid_int_request))
        self.assert200(self.send_request(self.valid_str_request))
        self.assertEqual(mock_enqueue.call_count, 2)

    def test_invalid_request(self, mock_enqueue):
        responses = self.send_6_invalid_requests()
        for response in responses:
            with self.subTest():
                self.assert422(response)
        mock_enqueue.assert_not_called()
