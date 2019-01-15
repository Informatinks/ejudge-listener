from unittest.mock import patch
from ejudge_listener.tasks import process_run
from tests.unit.base import TestCase

MONGO_PROTOCOL_ID = 1239


class Tasks(TestCase):
    def setUp(self):
        super().setUp()
        self.create_runs()

    @patch('ejudge_listener.tasks.put_protocol_to_mongo')
    def test_process_run(self, mock_put_protocol_to_mongo):
        mock_put_protocol_to_mongo.return_value = MONGO_PROTOCOL_ID

        process_run(1, 10)

        mock_put_protocol_to_mongo.assert_called()

    @patch('ejudge_listener.tasks.put_protocol_to_mongo')
    def test_process_run_failed(self, mock_put_protocol_to_mongo):
        mock_put_protocol_to_mongo.return_value = MONGO_PROTOCOL_ID

        with self.assertRaises(SystemExit) as cm:
            process_run(5555, 7777)

        self.assertEqual(cm.exception.code, 0)
