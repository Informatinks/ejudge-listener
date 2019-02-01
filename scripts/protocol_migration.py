import logging
import math

from pymongo import MongoClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ejudge_listener.exceptions import ProtocolNotFoundError
from ejudge_listener.models import EjudgeRun
from ejudge_listener.protocol.protocol import get_full_protocol
from scripts.config import DATABASE_URL, MONGO_URL

# Init logger
logger = logging.getLogger('protocol-migration')
file_handler = logging.FileHandler('protocol-migration.log')
file_handler.setLevel(logging.DEBUG)
log_fmt = '%(asctime)s - %(message)s'
file_format = logging.Formatter(log_fmt)
file_handler.setFormatter(file_format)

# MySQL
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

# Mongo
mongo = MongoClient(MONGO_URL)

LIMIT_ROWS = 1000


def process_protocol(run: EjudgeRun):
    try:
        protocol = get_full_protocol(run)
    except ProtocolNotFoundError:
        logger.error(f'Protocol({run.contest_id}, {run.run_id}) -')
    else:
        mongo.db.protocol.insert_one(protocol)
        logger.info(f'Protocol({run.contest_id}, {run.run_id}) +')


def migrate():
    total_chunks = math.ceil(session.query(EjudgeRun).count() / LIMIT_ROWS)

    first_run = session.query(EjudgeRun) \
        .order_by(EjudgeRun.contest_id, EjudgeRun.run_id) \
        .first()
    last_contest_id = first_run.contest_id
    last_run_id = first_run.run_id

    process_protocol(first_run)

    for _ in range(total_chunks):
        runs = session.query(EjudgeRun) \
            .filter(EjudgeRun.contest_id >= last_contest_id,
                    EjudgeRun.run_id > last_run_id) \
            .order_by(EjudgeRun.contest_id, EjudgeRun.run_id) \
            .limit(LIMIT_ROWS)
        for run in runs:
            process_protocol(run)
        last_contest_id = runs[-1].contest_id
        last_run_id = runs[-1].run_id


if __name__ == '__main__':
    migrate()
