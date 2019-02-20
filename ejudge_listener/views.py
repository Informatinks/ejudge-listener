from flask import request
from werkzeug.exceptions import BadRequest

from ejudge_listener.extensions import rq
from ejudge_listener.protocol.run_statuses import TERMINAL_RUN_STATUSES
from ejudge_listener.schemas import EjudgeRequestSchema
from ejudge_listener.utils import jsonify

ej_request_schema = EjudgeRequestSchema()


def update_run():
    ej_request, errors = ej_request_schema.load(request.args)
    if errors:
        raise BadRequest()
    print(ej_request)
    q = rq.get_queue('ejudge_listener')
    if ej_request.status in TERMINAL_RUN_STATUSES:
        q.enqueue('ejudge_listener.tasks.send_terminal_to_front', ej_request)
    else:
        q.enqueue('ejudge_listener.tasks.send_non_terminal_to_front', ej_request)
    return jsonify({})
