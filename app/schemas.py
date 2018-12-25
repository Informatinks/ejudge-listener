from marshmallow import Schema, fields


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
