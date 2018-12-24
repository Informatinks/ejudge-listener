import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:

    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    RQ_REDIS_URL = os.getenv('REDIS_URL', 'redis://')
    RQ_QUEUES = ['default']


class DevelopmentConfig(Config):
    DEBUG = True


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'

    RQ_CONNECTION_CLASS = 'fakeredis.FakeStrictRedis'
    RQ_ASYNC = True
