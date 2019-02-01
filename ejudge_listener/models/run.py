from sqlalchemy import Column, Integer

from ejudge_listener.models import db


class Run(db):
    __table_args__ = (
        {'schema': 'pynformatics'},
    )
    __tablename__ = 'runs'

    id = Column(Integer, primary_key=True)
    ejudge_run_id = Column('ej_run_id', Integer)
    ejudge_contest_id = Column('ej_contest_id', Integer)
