from typing import Optional

from flask import jsonify as flask_jsonify

from ejudge_listener.requests import EjudgeRequest


def jsonify(data, status_code=200):
    response = {'status_code': status_code}
    if status_code in (200, 201):
        response['data'] = data
        response['status'] = 'success'
    else:
        response['error'] = data
        response['status'] = 'error'

    return flask_jsonify(response), status_code


def make_log_message(
        func_name: str,
        task: str,
        request: EjudgeRequest,
        response_status: Optional[int] = None):
    """
    :param func_name: tasks's function name.
    :param task: success, failure, retry, revoked.
    :param request: request from ejudge.
    :param response_status: HTTP status if exists
    """
    request = str(request)
    string = f'{func_name}, ' \
        f'task: {task}, ' \
        f'request: {request!r}'
    status = response_status
    string += f', front_status: {status}' if status else ''
    return string
