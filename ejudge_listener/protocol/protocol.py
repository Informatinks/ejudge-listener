from collections import OrderedDict

from ejudge_listener.exceptions import ProtocolNotFoundError
from ejudge_listener.models.ejudge_run import EjudgeRun


def read_protocol(run: EjudgeRun) -> dict:
    tests_results = read_tests_results(run)
    audit = run.get_audit()
    tests_results['audit'] = audit
    return tests_results


def read_tests_results(run: EjudgeRun):
    try:
        run.fetch_tested_protocol_data()
        tests = OrderedDict()
        if run.tests:
            sample_tests = run.problem.sample_tests.split(',')
            for num in range(1, len(run.tests.keys()) + 1):
                str_num = str(num)
                if str_num in sample_tests:
                    tests[str_num] = run.get_test_full_protocol(str_num)
                else:
                    tests[str_num] = run.tests[str_num]
        for test_num in tests:
            tests[test_num] = run.get_test_full_protocol(test_num)
        return {'tests': tests, 'compiler_output': run.compiler_output}

    except Exception:
        raise ProtocolNotFoundError
