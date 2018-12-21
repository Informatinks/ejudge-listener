from flask import current_app
from webargs import fields
from webargs.flaskparser import use_args

from app.utils import jsonify

TASK_REFERENCE = 'app.tasks.send_run'

update_run_args = {
    'contest_id': fields.Int(required=True),
    'run_id': fields.Int(required=True),
}


@use_args(update_run_args)
def update_run(args):
    current_app.task_queue.enqueue(TASK_REFERENCE, **args)
    return jsonify({})
