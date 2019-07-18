from celery import shared_task
from celery.utils.log import get_task_logger
from requests import RequestException
from sqlalchemy.orm.exc import NoResultFound

from ejudge_listener import flow
from ejudge_listener.flow import is_4xx_error, mongo_rollback
from ejudge_listener.protocol.exceptions import ProtocolNotFoundError, TestsNotFoundError

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


@shared_task(bind=True, default_retry_delay=2, retry_backoff=True)
def load_protocol(self, request_args):
    """ Load Ejudge run from database and load protocol from filesystem for this run.
    """
    try:
        return flow.load_protocol(request_args)
    except NoResultFound:
        logger.error(f'Run not found. Request args={request_args}')
        self.request.chain = None  # Stop chain
    except TestsNotFoundError as exc:
        logger.warning(f'Tests not found. Retrying task. Request args={request_args}')
        raise self.retry(exc=exc)
    except ProtocolNotFoundError as exc:
        logger.warning(f'Protocol not found. Retrying task. Request args={request_args}')
        raise self.retry(exc=exc)


@shared_task
def insert_to_mongo(run_data):
    """ Insert to mongo protocol, return Ejudge run data with mongo id of new protocol.
    """
    return flow.insert_to_mongo(run_data)


@shared_task(bind=True, max_retries=None, retry_backoff=True)
def send_terminal(self, data):
    """Send Ejudge run data and mongo id of protocol.
    """
    try:
        flow.send_terminal(data)
    except RequestException as exc:
        if is_4xx_error(exc):
            logger.error('Received status 4xx from rmatics. Rollback mongo')
            mongo_rollback(data)
        else:
            logger.exception('Got unexpected error while request to rmatics. Retrying task')
            self.retry(exc=exc, countdown=2 * self.request.retries)
