from celery import Celery
from flask_pymongo import PyMongo
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
mongo = PyMongo()
celery = Celery("ejudge-listener")
celery.config_from_object('celeryconfig')
