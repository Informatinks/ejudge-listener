from marshmallow import Schema, fields


class EjudgeRunSchema(Schema):
    run_id = fields.Int()
    contest_id = fields.Int()
    run_uuid = fields.String()
    score = fields.Int()
    status = fields.Int()
    lang_id = fields.Int()
    test_num = fields.Int()
    create_time = fields.DateTime()
    last_change_time = fields.DateTime()
