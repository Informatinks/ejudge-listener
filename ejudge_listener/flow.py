from typing import NamedTuple, Tuple

import requests
from bson import ObjectId
from flask import current_app
from marshmallow import fields, Schema, post_load

from .models import EjudgeRun
from .extensions import mongo, db
from .protocol.protocol import read_protocol

REQUEST_TIMEOUT = 5  # seconds


class EjudgeRequest(NamedTuple):
    contest_id: int
    run_id: int
    status: int


class EjudgeRequestSchema(Schema):
    run_id = fields.Integer(required=True)
    contest_id = fields.Integer(required=True)
    status = fields.Integer(required=True, load_from="new_status")

    @post_load
    def make_request(self, data):
        return EjudgeRequest(**data)


class EjudgeRunSchema(Schema):
    run_id = fields.Integer()
    contest_id = fields.Integer()
    run_uuid = fields.String()
    score = fields.Integer()
    status = fields.Integer()
    lang_id = fields.Integer()
    test_num = fields.Integer()
    create_time = fields.DateTime()
    last_change_time = fields.DateTime()


ej_request_schema = EjudgeRequestSchema()
ej_run_schema = EjudgeRunSchema()


def send_non_terminal(request_args: dict) -> None:
    """Send non terminal status run."""
    requests.post(
        current_app.config['EJUDGE_FRONT_URL'],
        json=request_args,
        timeout=REQUEST_TIMEOUT,
    )


def load_protocol(request_args: dict) -> Tuple[dict, dict]:
    r, _ = ej_request_schema.load(request_args)
    run = (
        db.session.query(EjudgeRun)
        .filter_by(contest_id=r.contest_id, run_id=r.run_id)
        .one()
    )
    protocol = read_protocol(run)
    run_data = ej_run_schema.dump(run).data
    return run_data, protocol


def insert_to_mongo(run_data) -> dict:
    run_data, protocol = run_data
    mongo_protocol_id = insert_protocol_to_mongo(protocol)
    run_data['mongo_protocol_id'] = mongo_protocol_id
    return run_data


def send_terminal(run_data: dict):
    r = requests.post(
        current_app.config['EJUDGE_FRONT_URL'], json=run_data, timeout=REQUEST_TIMEOUT
    )
    r.raise_for_status()


def insert_protocol_to_mongo(protocol: dict) -> str:
    """
    Insert EjudgeRun load_protocol to mongo.
    :param protocol: EjudgeRun load_protocol.
    :return: hex encoded version of ObjectId.
    """
    protocol_id = mongo.db.protocol.insert_one(protocol).inserted_id
    mongo_protocol_id = str(protocol_id)
    return mongo_protocol_id


def mongo_rollback(data: dict) -> None:
    mongo_id = data['mongo_protocol_id']
    mongo.db.protocol.delete_one({'_id', ObjectId(mongo_id)})


def is_4xx_error(status_code) -> bool:
    return 400 <= status_code < 500
