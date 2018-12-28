from flask_testing import TestCase

from ejudge_listener import create_app
from config import TestConfig


class ViewTest(TestCase):
    def create_app(self):
        app = create_app(TestConfig)
        return app
