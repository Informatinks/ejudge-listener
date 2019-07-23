from collections import OrderedDict

from ejudge_listener.models import EjudgeRun
from ejudge_listener.protocol.exceptions import ProtocolNotFoundError, TestsNotFoundError


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
            for num in range(1, len(run.tests) + 1):
                str_num = str(num)
                tests[str_num] = run.get_test_full_protocol(str_num)
        return {'tests': tests, 'compiler_output': run.compiler_output}
    except TestsNotFoundError:
        # If tests not found, push it up by stack
        # to retry task over interval
        raise TestsNotFoundError
    except Exception:
        # If we raise any other eror, consider is as ProtocolNotFoundError
        # and safely fail task
        raise ProtocolNotFoundError
