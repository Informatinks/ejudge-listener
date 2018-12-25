from webargs import fields
from webargs.flaskparser import use_args

from app.plugins import rq
from app.utils import jsonify


update_run_args = {
    'contest_id': fields.Int(required=True),
    'run_id': fields.Int(required=True),
}


@use_args(update_run_args)
def update_run(args):
    rq.get_queue().enqueue('app.tasks.send_run', **args)
    return jsonify({})
