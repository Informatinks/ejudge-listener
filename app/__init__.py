from flask import Flask
from app.db import db
from app.error_handler import register_error_handlers
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
    return app
