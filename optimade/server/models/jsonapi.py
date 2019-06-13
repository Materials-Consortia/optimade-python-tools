"""
This module should reproduce https://jsonapi.org/schema
"""

from typing import Optional, Set, Union, Dict, Any
from pydantic import BaseModel, UrlStr, constr

class Link(BaseModel):
    href: UrlStr
    meta: Optional[dict]

class Links(BaseModel):
    next: Optional[Union[UrlStr,Link]]
    base_url: Optional[Union[UrlStr,Link]]

class JsonAPI(BaseModel):
    version: str
    meta: Optional[dict]

class Pagination(BaseModel):
    first: Optional[UrlStr]
    last: Optional[UrlStr]
    prev: Optional[UrlStr]
    next: Optional[UrlStr]

class Source(BaseModel):
    pointer: Optional[str]
    parmeter: Optional[str]

class Error(BaseModel):
    id: Optional[str]
    status: Optional[str]
    code: Optional[str]
    title: Optional[str]
    detail: Optional[str]
    source: Optional[Source]
    meta: Optional[dict]

class Failure(BaseModel):
    errors: Set[Error]
    meta: Optional[dict]
    jsonapi: Optional[JsonAPI]
    links: Optional[Links]

class Info(BaseModel):
    meta: dict
    jsonapi: Optional[JsonAPI]
    links: Optional[Links]

att_pat_prop = constr(regex=r'^(?!relationships$|links$|id$|type$)\\w[-\\w_]*$')
class Attributes(BaseModel):
    items: Optional[Dict[att_pat_prop, Any]]

class RelationshipLinks(BaseModel):
    self: Optional[Link]
    related: Optional[Link]

class Linkage(BaseModel):
    type: str
    id: str
    meta: Optional[dict]

class Relationship(BaseModel):
    links: Optional[RelationshipLinks]
    data: Optional[Union[Linkage, Set[Linkage]]]
    meta: Optional[dict]

rel_pat_prop = constr(regex=r"^(?!id$|type$)\\w[-\\w_]*$")
class Relationships(BaseModel):
    items : Optional[Dict[rel_pat_prop, Relationship]]

class Resource(BaseModel):
    id: str
    type: str
    links: Optional[Links]
    meta: Optional[dict]
    attributes: Optional[Attributes]
    relationships: Optional[Relationships]

class Success(BaseModel):
    data: Union[None, Resource, Set[Resource]]
    included: Optional[Set[Resource]]
    meta: Optional[dict]
    links: Optional[Union[Links, Pagination]]
    jsonapi: Optional[JsonAPI]

# FIXME: PLACEHOLDER
class Meta(BaseModel, Dict):
    pass
