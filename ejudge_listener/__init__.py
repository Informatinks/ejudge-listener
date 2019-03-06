from logging.config import dictConfig

from flask import Flask

import cli
from .api import register_error_handlers
from .routes import setup_routes
from .extensions import celery, mongo
from .extensions import db
# from .routes import setup_routes


def create_app():
    init_logger()
    app = Flask(__name__)
    app.config.from_pyfile('../configs/production.cfg', silent=True)
    db.init_app(app)
    mongo.init_app(app)
    configure_celery_app(app, celery)
    register_error_handlers(app)
    app.cli.add_command(cli.test)
    setup_routes(app)
    return app


def init_logger():
    dictConfig({
        'version': 1,
        'formatters': {
            'default': {
                'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
            },
        },
        'handlers': {
            'stdout': {
                'class': 'logging.StreamHandler',
                'formatter': 'default',
                'stream': 'ext://sys.stdout',
            },
        },
        'root': {
            'level': 'INFO',
            'handlers': ['stdout'],
        }
    })


def configure_celery_app(app, celery):
    """Configures the celery app."""
    celery.conf.update(app.config)
    celery.conf['imports'] = [
        'ejudge_listener.tasks'
    ]

    # noinspection PyPep8Naming
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask
