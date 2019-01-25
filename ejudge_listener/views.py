from webargs import fields
from webargs.flaskparser import use_args

from ejudge_listener.plugins import rq
from ejudge_listener.utils import jsonify

# noinspection PyUnresolvedReferences
update_run_args = {
    'contest_id': fields.Int(required=True),
    'run_id': fields.Int(required=True),
}


@use_args(update_run_args)
def update_run(args):
    rq.get_queue('ejudge_listener').enqueue('ejudge_listener.tasks.send_to_ejudge_front', **args)
    return jsonify({})
