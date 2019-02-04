import logging
import math
from typing import Optional

from sqlalchemy import Column, Integer, func

from ejudge_listener import create_app
from ejudge_listener.exceptions import (
    AuditNotFoundError,
    ProtocolNotFoundError
)
from ejudge_listener.extensions import mongo
from ejudge_listener.models import EjudgeRun
from ejudge_listener.models.base import db
from ejudge_listener.protocol.protocol import read_protocol


class Run(db.Model):
    __table_args__ = ({'schema': 'pynformatics'},)
    __tablename__ = 'runs'

    id = Column(Integer, primary_key=True)
    ejudge_run_id = Column('ej_run_id', Integer)
    ejudge_contest_id = Column('ej_contest_id', Integer)


# Init logger
logger = logging.getLogger('protocol-migration')
file_handler = logging.FileHandler('protocol-migration.log')
file_handler.setLevel(logging.DEBUG)
log_fmt = '%(asctime)s - %(message)s'
file_format = logging.Formatter(log_fmt)
file_handler.setFormatter(file_format)

# Init app
app = create_app()
app.app_context().push()

LIMIT_ROWS = 1_000


def get_ejudge_run(run: Run) -> Optional[EjudgeRun]:
    ejudge_run = db.session.query(EjudgeRun) \
        .filter(EjudgeRun.contest_id == run.ejudge_contest_id) \
        .filter(EjudgeRun.run_id == run.ejudge_run_id) \
        .one_or_none()
    return ejudge_run


def process_protocol(run: EjudgeRun):
    try:
        protocol = read_protocol(run)
    except AuditNotFoundError:
        logger.error(f'Protocol({run.contest_id}, {run.run_id}) audit -')
    except ProtocolNotFoundError:
        logger.error(f'Protocol({run.contest_id}, {run.run_id}) proto -')
    else:
        mongo.db.protocol.insert_one(protocol)
        logger.info(f'Protocol({run.contest_id}, {run.run_id}) +')


def migrate():
    count = db.session.query(Run).count()
    total_chunks = math.ceil(count / LIMIT_ROWS)
    last_id = db.session.query(func.min(Run.id)).scalar() - 1

    for _ in range(total_chunks):
        runs = db.session.query(Run) \
            .filter(Run.id > last_id) \
            .order_by(Run.id) \
            .limit(LIMIT_ROWS)
        for run in runs:
            ejudge_run = get_ejudge_run(run)
            if ejudge_run is not None:
                process_protocol(ejudge_run)
            else:
                msg = f'EjudgeRun({run.contest_id}, {run.run_id}) not found'
                logger.error(msg)

        last_id = runs[-1].id


if __name__ == '__main__':
    migrate()
