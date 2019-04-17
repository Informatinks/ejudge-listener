from ejudge_listener import create_app
from ejudge_listener.extensions import celery
from ejudge_listener.config import CONFIG_MODULE

# Prevent app factory to configure own logger
# as it breaks celery task default logger
# TODO: worker_hijack_root_logger or @after_setup_task_logger
app = create_app(CONFIG_MODULE, config_logger=False)
app.app_context().push()
