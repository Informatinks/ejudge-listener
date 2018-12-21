import random
import unittest
from unittest.mock import patch

from flask import url_for
from flask_testing import TestCase

from app import create_app
from config import TestConfig


def random_id():
    return random.randint(1, 1_000_000)


INVALID_IDS = ['', 'one', 'dog', True, False, None]


def random_invalid_id():
    return random.choice(INVALID_IDS)


@patch('app.views.current_app')
class ViewTest(TestCase):
    def create_app(self):
        app = create_app(TestConfig)
        return app

    valid_params = {'contest_id': 1, 'run_id': 10}
    valid_str_params = {'contest_id': "1", 'run_id': 10}
    invalid_values_params = {'contest_id': "one", 'run_id': "ten"}
    invalid_keys_params = {'dog_id': 1, 'cat_id': 10}

    def assert422(self, response, message=None):
        self.assertStatus(response, 422, message)

    def request(self, params):
        return self.client.get(url_for('update', **params))

    def request_many(self, *, valid=1, invalid=1):
        valid_responses = [
            self.request({'contest_id': random_id(), 'run_id': random_id()})
            for _ in range(valid)
        ]
        invalid_responses = [
            self.request(
                {'contest_id': random_invalid_id(), 'run_id': random_invalid_id()}
            )
            for _ in range(invalid)
        ]
        return valid_responses, invalid_responses

    # --------------------------------------------------------------------------

    def test_valid_request(self, mock_cur_app):
        self.assert200(self.request(self.valid_params))
        self.assert200(self.request(self.valid_str_params))
        v, _ = self.request_many(valid=50, invalid=0)

        for response in v:
            with self.subTest():
                self.assert200(response)

    def test_invalid_request(self, mock_cur_app):
        self.assertEqual(self.request(self.invalid_values_params).status_code, 422)
        self.assertEqual(self.request(self.invalid_keys_params).status_code, 422)
        _, i = self.request_many(valid=0, invalid=50)
        for response in i:
            with self.subTest():
                self.assert422(response)

    def test_task_enqueue(self, mock_cur_app):
        v, i = self.request_many(valid=20, invalid=80)
        tasks_queued = mock_cur_app.task_queue.enqueue.call_count
        self.assertEqual(tasks_queued, 20)


if __name__ == '__main__':
    unittest.main()
