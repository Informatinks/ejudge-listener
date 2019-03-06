from celery import shared_task
from celery.utils.log import get_task_logger
from requests import HTTPError, RequestException
from sqlalchemy.orm.exc import NoResultFound

from ejudge_listener import flow
from ejudge_listener.protocol.exceptions import ProtocolNotFoundError
from ejudge_listener.flow import is_4xx_error, mongo_rollback

logger = get_task_logger(__name__)


# NON TERMINAL
# -----------------------------------------------------------------------------
@shared_task(ignore_result=True, retry=False)
def send_non_terminal(request_args) -> None:
    flow.send_non_terminal(request_args)


# TERMINAL
# -----------------------------------------------------------------------------
@shared_task(bind=True, retry_backoff=True)
def load_protocol(self, request_args):
    try:
        return flow.load_protocol(request_args)
    except NoResultFound:
        msg = f'Unexpected error. Run not found. Request args={request_args}'
        logger.exception(msg)
        self.request.chain = None  # stop chain
    except ProtocolNotFoundError as exc:
        raise self.retry(exc=exc)


@shared_task
def insert_to_mongo(run_data):
    return flow.insert_to_mongo(run_data)


@shared_task(bind=True, max_retries=None, retry_backoff=True)
def send_terminal(self, data):
    try:
        flow.send_terminal(data)
    except HTTPError as exc:
        status_code = exc.response.status_code
        if is_4xx_error(status_code):
            mongo_rollback(data)
            msg = 'Unexpected error. Status 400 from ejudge front. Rollback mongo'
            logger.exception(msg)
        else:
            self.retry(exc=exc)
    except RequestException as exc:
        self.retry(exc=exc)
