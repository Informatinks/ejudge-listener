import rq
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from redis import Redis

from app.error_handler import register_error_handlers
from app.routes import setup_routes
from config import Config

db = SQLAlchemy()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    db.init_app(app)
    setup_routes(app)
    app.redis = Redis.from_url(app.config['REDIS_URL'])
    app.task_queue = rq.Queue('microblog-tasks', connection=app.redis)
    register_error_handlers(app)
    return app
