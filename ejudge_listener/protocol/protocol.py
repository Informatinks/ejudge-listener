import traceback
from collections import OrderedDict
from typing import Optional

from ejudge_listener.models.ejudge_run import EjudgeRun


def get_full_protocol(run: EjudgeRun) -> Optional[dict]:
    protocol = get_protocol(run)
    if protocol.get('result') == 'error':
        return protocol

    tests = protocol.get('tests', {})
    for test_num in tests:
        tests[test_num] = run.get_test_full_protocol(test_num)
    try:
        audit = run.get_audit()
    except FileNotFoundError:
        return None
    full_protocol = {'tests': tests, 'audit': audit}
    compiler_output = protocol.get('compiler_output')
    if compiler_output:
        full_protocol['compiler_output'] = protocol['compiler_output']

    return full_protocol


def get_protocol(run: EjudgeRun):
    try:
        run.fetch_tested_protocol_data()
        res = OrderedDict()
        if run.tests:
            sample_tests = run.problem.sample_tests.split(',')
            for num in range(1, len(run.tests.keys()) + 1):
                str_num = str(num)
                if str_num in sample_tests:
                    res[str_num] = run.get_test_full_protocol(str_num)
                else:
                    res[str_num] = run.tests[str_num]
        return {'tests': res, 'host': run.host, 'compiler_output': run.compiler_output}

    except Exception as e:
        return {
            'result': 'error',
            'message': run.compilation_protocol,
            'error': e.__str__(),
            'stack': traceback.format_exc(),
            'protocol': run.protocol,
        }
