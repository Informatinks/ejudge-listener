from flask import Flask, current_app

from ejudge_listener.error_handler import register_error_handlers
from ejudge_listener.models import db
from ejudge_listener.plugins import rq
from ejudge_listener.routes import setup_routes


def create_app(config_class=None):
    app = Flask(__name__)
    app.config.from_pyfile('../settings.cfg', silent=True)
    app.config.from_pyfile('../local-settings.cfg', silent=True)
    if config_class:
        app.config.from_object(config_class)

    db.init_app(app)
    rq.init_app(app)
    setup_routes(app)
    register_error_handlers(app)
    return app
