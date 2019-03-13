from flask import request

from ejudge_listener.flow import EjudgeRequestSchema
from ejudge_listener.protocol import run
from ejudge_listener.api import jsonify
from ejudge_listener.tasks import (
    send_non_terminal,
    load_protocol,
    insert_to_mongo,
    send_terminal,
)

send_terminal_chain = load_protocol.s() | insert_to_mongo.s() | send_terminal.s()

ej_request_schema = EjudgeRequestSchema()


def update_run():
    request_args, _ = ej_request_schema.load(request.args)
    json_args, _ = ej_request_schema.dump(request_args)
    isterminal = request_args.status in run.TERMINAL_STATUSES
    if isterminal:
        send_terminal_chain.delay(json_args)
    else:
        send_non_terminal.delay(json_args)
    return jsonify({})
