from unittest.mock import patch

from ejudge_listener.models import EjudgeRun
from ejudge_listener.protocol.exceptions import TestsNotFoundError
from tests.unit.base import TestCase


class TestReadTests(TestCase):
    @patch('ejudge_listener.models.EjudgeRun._get_protocol')
    def test_should_raise_if_empty_protocol(self, _get_protocol):
        run = EjudgeRun(contest_id=1, run_id=1)
        _get_protocol.return_value = ''

        with self.assertRaises(TestsNotFoundError):
            run.fetch_tested_protocol_data()

    @patch('ejudge_listener.models.EjudgeRun._get_protocol')
    def test_should_raise_if_invalid_xml(self, _get_protocol):
        run = EjudgeRun(contest_id=1, run_id=1)
        _get_protocol.return_value = 'INVALID XML'

        with self.assertRaises(TestsNotFoundError):
            run.fetch_tested_protocol_data()

    @patch('ejudge_listener.models.EjudgeRun._get_protocol')
    def test_should_raise_if_no_report_node(self, _get_protocol):
        run = EjudgeRun(contest_id=1, run_id=1)
        _get_protocol.return_value = '''Content-type: text/xml

        <?xml version="1.0" encoding="utf-8"?>'''

        with self.assertRaises(TestsNotFoundError):
            run.fetch_tested_protocol_data()

    @patch('ejudge_listener.models.EjudgeRun._get_protocol')
    def test_should_raise_if_no_tests_node(self, _get_protocol):
        run = EjudgeRun(contest_id=1, run_id=1)
        _get_protocol.return_value = '''Content-type: text/xml

        <?xml version="1.0" encoding="utf-8"?>
        <testing-report run-id="46" judge-id="44" status="OK" scoring="KIROV" run-tests="66" contest-id="2233" real-time-available="yes" max-memory-used-available="yes" correct-available="yes" tests-passed="66" score="100" max-score="100" time-limit-ms="1000" real-time-limit-ms="5000" marked-flag="no" >
          <uuid>65e9229d-be59-4c37-92b6-8729b20929d5</uuid>
          <host>vm-02-04</host>
          <cpu-model>Intel Core Processor (Haswell)</cpu-model>
          <cpu-mhz>3299.996</cpu-mhz>
          <compiler_output></compiler_output>
        </testing-report>'''

        with self.assertRaises(TestsNotFoundError):
            run.fetch_tested_protocol_data()

    @patch('ejudge_listener.models.EjudgeRun._get_protocol')
    def test_should_raise_if_zero_tests(self, _get_protocol):
        run = EjudgeRun(contest_id=1, run_id=1)
        _get_protocol.return_value = '''Content-type: text/xml

        <?xml version="1.0" encoding="utf-8"?>
        <testing-report run-id="46" judge-id="44" status="OK" scoring="KIROV" run-tests="66" contest-id="2233" real-time-available="yes" max-memory-used-available="yes" correct-available="yes" tests-passed="66" score="100" max-score="100" time-limit-ms="1000" real-time-limit-ms="5000" marked-flag="no" >
          <uuid>65e9229d-be59-4c37-92b6-8729b20929d5</uuid>
          <host>vm-02-04</host>
          <cpu-model>Intel Core Processor (Haswell)</cpu-model>
          <cpu-mhz>3299.996</cpu-mhz>
          <compiler_output></compiler_output>
          <tests>

          </tests>
        </testing-report>'''

        with self.assertRaises(TestsNotFoundError):
            run.fetch_tested_protocol_data()
