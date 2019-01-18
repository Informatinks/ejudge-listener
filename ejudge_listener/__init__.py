from flask import Flask

from ejudge_listener.error_handler import register_error_handlers
from ejudge_listener.models import db
from ejudge_listener.plugins import rq, mongo
from ejudge_listener.routes import setup_routes


def create_app(is_test=False):
    app = Flask(__name__)
    if is_test:
        app.config.from_pyfile('../settings/test-settings.cfg', silent=True)
    else:
        app.config.from_pyfile('../settings/settings.cfg', silent=True)

    db.init_app(app)
    mongo.init_app(app)
    rq.init_app(app)
    setup_routes(app)
    register_error_handlers(app)
    return app
