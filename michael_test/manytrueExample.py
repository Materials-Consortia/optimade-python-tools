from marshmallow_jsonapi import Schema, fields
from marshmallow import pprint
class User:
    def __init__(self, id, name):
        self.id = id
        self.name = name
class Comment:
    def __init__(self, id, body, author):
        self.id = id
        self.body = body
        self.author = author
class Post:
    def __init__(self, id, title, author, comments=None):
        self.id = id
        self.title = title
        self.author = author # User object
        self.comments = [] if comments is None else comments # Comment objects

class PostSchema(Schema):
    id = fields.Str(dump_only=True)
    title = fields.Str()
    comments = fields.Relationship(
        related_url='/posts/{post_id}/comments',
        related_url_kwargs={'post_id': '<id>'},
        many=True, include_resource_linkage=True,
        type_='comments',
        # define a schema for rendering included data
        schema='CommentSchema'
        )
    author = fields.Relationship(
        self_url='/posts/{post_id}/relationships/author',
        self_url_kwargs={'post_id': '<id>'},
        related_url='/authors/{author_id}',
        related_url_kwargs={'author_id': '<author.id>'},
        include_resource_linkage=True,
        type_='users'
        )
    class Meta:
        type_ = 'posts'
        strict = True
class CommentSchema(Schema):
    id = fields.Str(dump_only=True)
    body = fields.Str()
    author = fields.Relationship(
        self_url='/comments/{comment_id}/relationships/author',
        self_url_kwargs={'comment_id': '<id>'},
        related_url='/comments/{author_id}',
        related_url_kwargs={'author_id': '<author.id>'},
        type_='users',
        # define a schema for rendering included data
        schema='UserSchema',
    )
    class Meta:
        type_ = 'comments'
        strict = True
class UserSchema(Schema):
    id = fields.Str(dump_only=True)
    name = fields.Str()
    class Meta:
        type_ = 'users'
        strict = True

armin = User(id='101', name='Armin')
laura = User(id='94', name='Laura')
steven = User(id='23', name='Steven')
comments = [Comment(id='5', body='Marshmallow is sweet like sugar!', author=steven),
Comment(id='12', body='Flask is Fun!', author=armin)]
# pprint(comments)
post = Post(id='1', title='Django is Omakase', author=laura, comments=comments)
# print(post.comments)
pprint(PostSchema(include_data=('comments', 'comments.author')).dump(post).data)
