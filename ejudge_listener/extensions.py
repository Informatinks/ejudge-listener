from celery import Celery
from flask_pymongo import PyMongo
from flask_sqlalchemy import SQLAlchemy

from ejudge_listener.config import CONFIG_MODULE

db = SQLAlchemy()
mongo = PyMongo()
celery = Celery('ejudge-listener')
celery.config_from_object(CONFIG_MODULE)
