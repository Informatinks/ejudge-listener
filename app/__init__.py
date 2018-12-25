from flask import Flask, current_app

from app.error_handler import register_error_handlers
from app.models import db
from app.plugins import rq
from app.routes import setup_routes
from config import Config


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    rq.init_app(app)
    setup_routes(app)
    register_error_handlers(app)
    current_app.logger.info("App created")
    return app
