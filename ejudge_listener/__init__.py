from logging.config import dictConfig

from flask import Flask

import cli
from ejudge_listener.api import register_error_handlers
from ejudge_listener.config import CONFIG_MODULE
from ejudge_listener.extensions import celery, mongo
from ejudge_listener.extensions import db
from ejudge_listener.views import update_run


def create_app(config, config_logger=True):
    # Optional logger setup to prevent overriding
    # child applications own loggers
    if config_logger is True:
        init_logger()

    app = Flask(__name__)

    app.config.from_object(config)
    app.url_map.strict_slashes = False
    app.logger.info(f'Running with {config} module')

    db.init_app(app)
    mongo.init_app(app)
    configure_celery_app(app, celery)

    register_error_handlers(app)

    app.cli.add_command(cli.test)
    setup_routes(app)

    return app


def init_logger():
    dictConfig(
        {
            'version': 1,
            'formatters': {
                'default': {
                    'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
                }
            },
            'handlers': {
                'stdout': {
                    'class': 'logging.StreamHandler',
                    'formatter': 'default',
                    'stream': 'ext://sys.stdout',
                }
            },
            '': {'level': 'INFO', 'handlers': ['stdout']},
        }
    )


def configure_celery_app(app, celery):
    """Configures the celery app.
    """
    celery.conf.update(app.config)
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                try:
                    return TaskBase.__call__(self, *args, **kwargs)
                finally:
                    db.session.rollback()

    celery.Task = ContextTask


def setup_routes(app):
    app.add_url_rule('/notification/update_run', view_func=update_run)
