import xml

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


@shared_task(bind=True, default_retry_delay=3, max_retries=5)
def load_protocol(self, request_args):
    """ Load Ejudge run from database and load protocol from filesystem for this run.
    """
    try:
        return flow.load_protocol(request_args)

    except NoResultFound:
        logger.error(f'Run not found. Aborting task. Request args={request_args}')
        self.request.chain = None  # Stop chain

    except xml.parsers.expat.ExpatError:
        logger.exception(f'XML parsing error. Aborting task. Request args={request_args}')
        self.request.chain = None

    except TestsNotFoundError as exc:
        if self.request.retries < load_protocol.max_retries:
            raise self.retry(exc=exc)
        logger.warning('Tests not found. Max retries count exceed. Aborting.'
                       f'Request args={request_args}')
        self.request.chain = None

    except ProtocolNotFoundError as exc:
        if self.request.retries < load_protocol.max_retries:
            raise self.retry(exc=exc)
        logger.warning('Protocol not found. Max retries count exceed. Aborting.'
                       f'Request args={request_args}')
        self.request.chain = None


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
