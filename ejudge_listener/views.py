import functools

from flask import request

from ejudge_listener.api import jsonify
from ejudge_listener.flow import EjudgeRequestSchema
from ejudge_listener.protocol import run

ej_request_schema = EjudgeRequestSchema()


do_once = functools.lru_cache(1)


@do_once
def make_non_terminal_chain():
    """
    Returns chain for sending celery task for non terminal statuses,
    e.g. Compiling.
    Cache for only once module importing
    """
    from ejudge_listener.tasks import (
        send_non_terminal,
    )

    send_non_terminal_chain = send_non_terminal.s()
    return send_non_terminal_chain


@do_once
def make_terminal_chain():
    """
    Returns chain for sending celery task for terminal statuses,
    e.g. CE, OK.
    Cache for only once module importing
    """
    from ejudge_listener.tasks import (
        load_protocol,
        insert_to_mongo,
        send_terminal,
    )

    send_terminal_chain = load_protocol.s() | insert_to_mongo.s() | send_terminal.s()
    return send_terminal_chain


def update_run():
    request_args, _ = ej_request_schema.load(request.args)
    json_args, _ = ej_request_schema.dump(request_args)
    isterminal = request_args.status in run.TERMINAL_STATUSES

    send_non_terminal_chain = make_non_terminal_chain()
    send_terminal_chain = make_terminal_chain()

    if isterminal:
        send_terminal_chain.delay(json_args)
    else:
        send_non_terminal_chain.delay(json_args)
    return jsonify({})
