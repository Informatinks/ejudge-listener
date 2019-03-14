from celery import shared_task
from celery.utils.log import get_task_logger
from requests import RequestException
from sqlalchemy.orm.exc import NoResultFound

from ejudge_listener import flow
from ejudge_listener.flow import is_4xx_error, mongo_rollback
from ejudge_listener.protocol.exceptions import ProtocolNotFoundError

logger = get_task_logger(__name__)


@shared_task(ignore_result=True, retry=False)
def send_non_terminal(request_args):
    """Send non terminal status to ejudge front.

    We ignore result and not retry, because we get new status
    from ejudge earlier, then requeued task starts execute.
    And we just don't care about non terminal statuses, because
    main logic around terminal statuses and we can afford to not
    send or loose some of non terminal statuses to ejudge front.
    """
    flow.send_non_terminal(request_args)


@shared_task(bind=True, retry_backoff=True)
def load_protocol(self, request_args):
    """
    Load Ejudge run from database and load protocol from filesystem for this run.
    """
    try:
        return flow.load_protocol(request_args)
    except NoResultFound:
        self.request.chain = None  # Stop chain
        msg = f'Unexpected error. Run not found. Request args={request_args}'
        logger.exception(msg)
    except ProtocolNotFoundError as exc:
        raise self.retry(exc=exc, countdown=2)


@shared_task
def insert_to_mongo(run_data):
    """
    Insert to mongo protocol, return Ejudge run data with mongo id of new protocol.
    """
    return flow.insert_to_mongo(run_data)


@shared_task(bind=True, max_retries=None, retry_backoff=True)
def send_terminal(self, data):
    """Send Ejudge run data and mongo id of protocol."""
    try:
        flow.send_terminal(data)
    except RequestException as exc:
        if is_4xx_error(exc):
            mongo_rollback(data)
            msg = 'Unexpected error. Status 4xx from ejudge front. Rollback mongo'
            logger.exception(msg)
        else:
            self.retry(exc=exc, countdown=2)
