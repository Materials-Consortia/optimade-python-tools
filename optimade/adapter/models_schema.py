from marshmallow_jsonapi import Schema, fields
from models_class import  *

class StructureSchema(Schema):
    """Marshmallow-jsonapi schema that specifies a structure

    Follows tightly with OptimadeAPI's JSON API response specification
    http://www.optimade.org/optimade#h.4.1.2
    
    """
    id = fields.Str(dump_only = True)
    elements = fields.List(fields.Str())
    nelements = fields.Integer()
    pretty_formula = fields.Str(dump_to = "formula_prototype") # changing back to optimade name
    formula_anonymous = fields.Str(dump_to = "chemical_formula") # changing back to optimade name
    material_id = fields.Str()

    class Meta:
        type_ = 'structure'
        strict = True
