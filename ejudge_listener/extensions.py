from celery import Celery
from flask_pymongo import PyMongo
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
mongo = PyMongo()
celery = Celery(
    "ejudge-listener",
    broker='redis://@localhost:6379/0',
    backend='redis://@localhost:6379/0',
)
# celery = Celery()
