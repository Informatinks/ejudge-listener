from ejudge_listener import create_app
# noinspection PyUnresolvedReferences
from ejudge_listener.extensions import celery
from ejudge_listener.config import CONFIG_MODULE

app = create_app(CONFIG_MODULE)
app.app_context().push()
