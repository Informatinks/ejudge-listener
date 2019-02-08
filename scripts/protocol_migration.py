import concurrent.futures
import math
from typing import Optional

from pymongo.errors import InvalidOperation
from sqlalchemy import Column, Integer, func
from sqlalchemy.orm import joinedload

from ejudge_listener import create_app
from ejudge_listener.exceptions import AuditNotFoundError, ProtocolNotFoundError
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


# Init app
app = create_app()
app.app_context().push()

LIMIT_ROWS = 1000
LAST_ID = -1


def process_protocol(ejudge_run_and_run) -> Optional[dict]:
    global LAST_ID
    ej_run = ejudge_run_and_run[0]
    run_id = ejudge_run_and_run[1].id
    LAST_ID = run_id
    try:
        protocol = read_protocol(ej_run)
        protocol['run_id'] = run_id
    except AuditNotFoundError:
        print(f'Run({run_id}), Protocol({ej_run.contest_id}, {ej_run.run_id}) audit -')
    except ProtocolNotFoundError:
        print(f'Run({run_id}), Protocol({ej_run.contest_id}, {ej_run.run_id}) proto -')
    else:
        print(f'Run({run_id}), Protocol({ej_run.contest_id}, {ej_run.run_id}) +')
        return protocol


def migrate(start_with_run_id: int = None):
    global LAST_ID
    if start_with_run_id:
        LAST_ID = start_with_run_id
        count = db.session.query(Run).filter(Run.id > LAST_ID).count()
    else:
        count = db.session.query(Run).count()
        LAST_ID = db.session.query(func.min(Run.id)).scalar() - 1

    print(f'Script starts.. Last run_id={LAST_ID}, ids remaining={count}')
    total_chunks = math.ceil(count / LIMIT_ROWS)

    for _ in range(total_chunks):
        runs = (
            db.session.query(EjudgeRun, Run)
            .filter(EjudgeRun.contest_id == Run.ejudge_contest_id)
            .filter(EjudgeRun.run_id == Run.ejudge_run_id)
            .filter(Run.id > LAST_ID)
            .order_by(Run.id)
            .limit(LIMIT_ROWS)
            .options(joinedload(EjudgeRun.problem))
        )

        with concurrent.futures.ProcessPoolExecutor() as executor:
            protocols = executor.map(process_protocol, runs)
        not_empty_protocols = filter(None, protocols)

        try:
            mongo.db.protocol.insert_many(not_empty_protocols)
        except InvalidOperation:
            pass


if __name__ == '__main__':
    migrate()
