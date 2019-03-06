from ejudge_listener import create_app
# noinspection PyUnresolvedReferences
from ejudge_listener.extensions import celery

app = create_app()
