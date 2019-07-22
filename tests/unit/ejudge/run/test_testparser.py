import xml
from unittest.mock import patch, PropertyMock

from ejudge_listener.models import EjudgeRun
from ejudge_listener.protocol.exceptions import TestsNotFoundError
from tests.unit.base import TestCase


class TestReadTests(TestCase):
    @patch('ejudge_listener.models.EjudgeRun.protocol', new_callable=PropertyMock)
    def test_should_raise_if_empty_protocol(self, protocol):
        run = EjudgeRun(contest_id=1, run_id=1)
        protocol.return_value = ''

        with self.assertRaises(xml.parsers.expat.ExpatError):
            run.fetch_tested_protocol_data()

    @patch('ejudge_listener.models.EjudgeRun.protocol', new_callable=PropertyMock)
    def test_should_raise_if_no_report_node(self, protocol):
        run = EjudgeRun(contest_id=1, run_id=1)
        protocol.return_value = '''<?xml version="1.0" encoding="utf-8"?>'''

        with self.assertRaises(xml.parsers.expat.ExpatError):
            run.fetch_tested_protocol_data()

    @patch('ejudge_listener.models.EjudgeRun.protocol', new_callable=PropertyMock)
    def test_should_raise_if_no_tests_node(self, protocol):
        run = EjudgeRun(contest_id=1, run_id=1)
        protocol.return_value = '''<?xml version="1.0" encoding="utf-8"?>
        <testing-report run-id="46" judge-id="44" status="OK" scoring="KIROV" run-tests="66" contest-id="2233" real-time-available="yes" max-memory-used-available="yes" correct-available="yes" tests-passed="66" score="100" max-score="100" time-limit-ms="1000" real-time-limit-ms="5000" marked-flag="no" >
          <uuid>65e9229d-be59-4c37-92b6-8729b20929d5</uuid>
          <host>vm-02-04</host>
          <cpu-model>Intel Core Processor (Haswell)</cpu-model>
          <cpu-mhz>3299.996</cpu-mhz>
          <compiler_output></compiler_output>
        </testing-report>'''

        with self.assertRaises(TestsNotFoundError):
            run.fetch_tested_protocol_data()

    @patch('ejudge_listener.models.EjudgeRun.protocol', new_callable=PropertyMock)
    def test_should_raise_if_zero_tests(self, protocol):
        run = EjudgeRun(contest_id=1, run_id=1)
        protocol.return_value = '''<?xml version="1.0" encoding="utf-8"?>
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

    @patch('ejudge_listener.models.EjudgeRun.protocol', new_callable=PropertyMock)
    def test_should_parse_valid_xml(self, protocol):
        run = EjudgeRun(contest_id=1, run_id=1)
        protocol.return_value = '''<?xml version="1.0" encoding="utf-8"?>
        <testing-report run-id="46" judge-id="44" status="OK" scoring="KIROV" run-tests="66" contest-id="2233"
                        real-time-available="yes" max-memory-used-available="yes" correct-available="yes" tests-passed="66"
                        score="100" max-score="100" time-limit-ms="1000" real-time-limit-ms="5000" marked-flag="no">
            <uuid>65e9229d-be59-4c37-92b6-8729b20929d5</uuid>
            <host>vm-02-04</host>
            <cpu-model>Intel Core Processor (Haswell)</cpu-model>
            <cpu-mhz>3299.996</cpu-mhz>
            <compiler_output></compiler_output>
            <tests>
                <test num="1" status="OK" time="0" real-time="1" max-memory-used="1806336" nominal-score="0" score="0"
                      checker-comment="OK">
                    <program-stats-str>{ utime=0, stime=0, ptime=0, rtime=1, maxvsz=1806336, maxrss=7340032, nvcsw=1, nivcsw=4
                        }
                    </program-stats-str>
                    <checker-stats-str>{ utime=0, stime=0, ptime=0, rtime=5, maxvsz=335872, maxrss=7340032, nvcsw=3, nivcsw=8
                        }
                    </checker-stats-str>
                    <input size="17">5
                        01
                        10
                        01
                        01
                        10
                    </input>
                    <output size="2">0
                    </output>
                    <correct size="2">0
                    </correct>
                    <stderr size="0"></stderr>
                    <checker size="3">OK
                    </checker>
                </test>
                <test num="2" status="OK" time="0" real-time="1" max-memory-used="1806336" nominal-score="0" score="0"
                      checker-comment="OK">
                    <program-stats-str>{ utime=0, stime=0, ptime=0, rtime=1, maxvsz=1806336, maxrss=7340032, nvcsw=1, nivcsw=1
                        }
                    </program-stats-str>
                    <checker-stats-str>{ utime=0, stime=0, ptime=0, rtime=4, maxvsz=335872, maxrss=7340032, nvcsw=3, nivcsw=7
                        }
                    </checker-stats-str>
                    <input size="22">5
                        120
                        102
                        210
                        021
                        012
                    </input>
                    <output size="2">1
                    </output>
                    <correct size="2">1
                    </correct>
                    <stderr size="0"></stderr>
                    <checker size="3">OK
                    </checker>
                </test>
            </tests>
        </testing-report>'''

        try:
            run.fetch_tested_protocol_data()
            assert run.test_count == 2, 'should parse 2 tests'
            assert len(run.tests) == 2, 'should parse 2 tests'
        except TestsNotFoundError as exc:
            self.fail('should not raise TestsNotFoundError for valid XML')
