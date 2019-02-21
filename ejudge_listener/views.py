from flask import request
from werkzeug.exceptions import BadRequest

from ejudge_listener.extensions import rq
from ejudge_listener.schemas import EjudgeRequestSchema
from ejudge_listener.utils import jsonify

ej_request_schema = EjudgeRequestSchema()


def update_run():
    ej_request, errors = ej_request_schema.load(request.args)
    if errors:
        raise BadRequest()
    q = rq.get_queue('ejudge_listener')
    q.enqueue('ejudge_listener.tasks.send_to_front', ej_request)
    return jsonify({})
