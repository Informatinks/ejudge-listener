from flask import Flask

import cli
from ejudge_listener.error_handler import register_error_handlers
from ejudge_listener.extensions import rq, mongo
from ejudge_listener.logger import init_logger
from ejudge_listener.models import db
from ejudge_listener.routes import setup_routes


def create_app():
    init_logger()
    app = Flask(__name__)
    app.config.from_pyfile('../configs/production.cfg', silent=True)
    db.init_app(app)
    rq.init_app(app)
    setup_routes(app)
    register_error_handlers(app)
    app.cli.add_command(cli.test)
    return app
