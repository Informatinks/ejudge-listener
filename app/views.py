from flask import current_app
from webargs import fields
from webargs.flaskparser import use_args

from app.utils import jsonify

update_run_args = {
    'contest_id': fields.Int(required=True),
    'run_id': fields.Int(required=True),
}

TASK_REFERENCE = 'app.tasks.send_run'


@use_args(update_run_args)
def update(args):
    contest_id = args['contest_id']
    run_id = args['run_id']

    current_app.task_queue.enqueue(TASK_REFERENCE, contest_id, run_id)
    return jsonify({})
