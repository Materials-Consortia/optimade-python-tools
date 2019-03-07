from marshmallow_jsonapi import Schema, fields
from marshmallow import pprint
class Structure():
    def __init__(self, **kwargs):
        content = kwargs.get('param')
        if(content != None):
            self.id = content.get('material_id')
            self.elements = content.get('elements')
            self.nelements = content.get('nelements')
            self.pretty_formula = content.get('pretty_formula')
            self.formula_anonymous = content.get('formula_anonymous')
class Post:
    def __init__(self, id, structures=None):
        self.id = id
        self.structures = [] if structures is None else structures # Comment objects

class PostSchema(Schema):
    id = fields.Str(dump_only=True)
    title = fields.Str()
    comments = fields.Relationship(
        related_url='/posts/{post_id}/comments',
        related_url_kwargs={'post_id': '<id>'},
        many=True, include_resource_linkage=True,
        type_='structure',
        # define a schema for rendering included data
        schema='StructureSchema'
        )
    class Meta:
        type_ = 'posts'
        strict = True
class StructureSchema(Schema):
    id = fields.Str(dump_only = True)
    elements = fields.List(fields.Str())
    nelements = fields.Integer()
    pretty_formula = fields.Str()
    formula_anonymous = fields.Str()

    class Meta:
        type_ = 'structure'
        strict = True

structures = [Structure()]
# pprint(comments)
post = Post(id='1', structures=structures)
# print(post.comments)
pprint(PostSchema(include_data=('structures')).dump(post).data)
