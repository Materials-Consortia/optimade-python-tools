from marshmallow_jsonapi import Schema, fields
from models_class import  *

class LinksSchema(Schema):
    id = fields.Str(dump_only=True)
    next = fields.String()
    base_url = fields.String()
    class Meta:
        type_ = "links"
        strict = True

class MetaSchema(Schema):
    id = fields.Str(dump_only=True)
    query = fields.Dict()
    api_version = fields.String()
    time_stamp = fields.String()
    data_returned = fields.Integer()
    more_data_available = fields.Boolean()
    data_available = fields.Integer()
    last_id = fields.String()
    response_message = fields.String()
    class Meta:
        type_= "meta"
        strict = True
        ordered = True

class ResponseSchema(Schema):
    id = fields.Str(dump_only=True)
    links = fields.Dict()
    meta = fields.Dict()
    data = fields.Dict()
    class Meta:
        type_ = "response"
        ordered = True
