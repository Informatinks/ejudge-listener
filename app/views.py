from webargs import fields
from webargs.flaskparser import use_args

from app.tasks import send_run
from app.utils import jsonify

TASK_REFERENCE = 'app.tasks.send_run'

update_run_args = {
    'contest_id': fields.Int(required=True),
    'run_id': fields.Int(required=True),
}


@use_args(update_run_args)
def update_run(args):
    send_run.queue(TASK_REFERENCE, **args)
    return jsonify({})
