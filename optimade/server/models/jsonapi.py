"""
This module should reproduce https://jsonapi.org/schema
"""
from typing import Optional, List, Union

from pydantic import BaseModel, UrlStr


class Link(BaseModel):
    href: UrlStr
    meta: Optional[dict]

class Links(BaseModel):
    next: Optional[Link]

class Resource(BaseModel):
    id: str
    type: str
    attributes: Optional[Attributes]
    relationships : Optional[Relationships]
    links: Optional[Links]
    meta: Optional[dict]

class Success(BaseModel):
    data: Data
    included: Optional[List[Resource]]
    uniqueItems: bool = True
    meta: Optional[dict]
    links: Optional[Union[Links, Pagination]]
    jsonapi: Optional[Jsonapi]

class Failure(BaseModel):
    errors: List[Error]
    meta: Optional[dict]
    jsonapi: Optional[Jsonapi]
    links: Optional[Links]

class Info(BaseModel):
    meta: dict
    jsonapi: Optional[Jsonapi]
    links: Optional[Links]

class Data(List[Resource]):

class RelationshipLinks(BaseModel):
    self: Optional[Link]
    related: Optional[Link]

class Attributes(BaseModel):

class Relationships(BaseModel):

class RelationshipToOne(BaseModel):

class RelationshipToMany(BaseModel):

class Empty(None):

class Linkage(BaseModel):
    type: str
    id: str
    meta: Optional[dict]

class Pagination(BaseModel):
    first: Optional[UrlStr, None]
    last: Optional[UrlStr, None]
    prev: Optional[UrlStr, None]
    next: Optional[UrlStr, None]

class Jsonapi(BaseModel):
    version: str
    meta: Optional[dict]
class Error(BaseModel):
    id: str
    status: str
    code: str
    title: str
    detail: str
    meta: dict