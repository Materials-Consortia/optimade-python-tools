from marshmallow_jsonapi import Schema, fields
from models_class import  *

class StructureSchema(Schema):
    id = fields.Str(dump_only = True)
    elements = fields.List(fields.Str())
    nelements = fields.Integer()
    pretty_formula = fields.Str()
    formula_anonymous = fields.Str()
    material_id = fields.Str()

    class Meta:
        type_ = 'structure'
        strict = True
