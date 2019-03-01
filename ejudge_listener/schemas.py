from marshmallow import Schema, fields, post_load

from ejudge_listener.requests import EjudgeRequest


class EjudgeRequestSchema(Schema):
    run_id = fields.Integer(required=True)
    contest_id = fields.Integer(required=True)
    status = fields.Integer(required=True, load_from='new_status')

    @post_load
    def _(self, data):
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
    mongo_protocol_id = fields.String()
