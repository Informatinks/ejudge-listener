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


class LogMessage:
    def __init__(
        self,
        func_name: str,
        task: str,
        request: EjudgeRequest,
        front_status: Optional[int] = None,
    ):
        """
        :param func_name: tasks's function name.
        :param task: success, failure, retry, revoked.
        :param request: request from ejudge.
        """
        self.func_name = func_name
        self.task = task
        self.request = str(request)
        self.front_status = front_status

    def __str__(self):
        string = f'func_name: {self.func_name}, ' \
            f'task: {self.task}, ' \
            f'request: {self.request!r}'
        status = self.front_status
        string += f', front_status: {status}' if status else ''
        return string
