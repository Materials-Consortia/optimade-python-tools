"""
This module should reproduce https://jsonapi.org/schema
"""
from typing import Optional, Set, Union, Dict, Any
from pydantic import BaseModel, UrlStr, constr

class Meta(Dict[str, Any]):
    """Non-standard meta-information that can not be represented as an attribute or relationship."""

class Link(BaseModel):
    """A link **MUST** be represented as either: a string containing the link's URL or a link object."""
    href: UrlStr
    meta: Optional[dict]

class Links(BaseModel):
    """A Links object is a set of keys with a Link value"""
    next: Optional[Union[UrlStr,Link]]
    self: Optional[Union[UrlStr,Link]]
    about: Optional[Union[UrlStr, Link]]

class JsonAPI(BaseModel):
    """An object describing the server's implementation"""
    version: str
    meta: Optional[dict]

class Pagination(BaseModel):
    """
    A set of urls to different pages:
        first:The first page of data
        last:The last page of data
        prev:The previous page of data
        next:The next page of data
    """
    first: Optional[UrlStr]
    last: Optional[UrlStr]
    prev: Optional[UrlStr]
    next: Optional[UrlStr]

class Source(BaseModel):
    """A source object used in the Error type"""
    pointer: Optional[str]
    parmeter: Optional[str]

class Error(BaseModel):
    """
    An error response
    id: A unique identifier for this particular occurrence of the problem.
    links: A links object
    status: The HTTP status code applicable to this problem, expressed as a string value.
    code: An application-specific error code, expressed as a string value.
    title: A short, human-readable summary of the problem. It **SHOULD NOT** change from occurrence to occurrence of the problem, except for purposes of localization.
    detail: A human-readable explanation specific to this occurrence of the problem.
    source: A source
    meta: A meta dict
    """
    id: Optional[str]
    status: Optional[str]
    code: Optional[str]
    title: Optional[str]
    detail: Optional[str]
    source: Optional[Source]
    meta: Optional[dict]
    links: Optional[Links]

class Failure(BaseModel):
    """A failure object"""
    errors: Set[Error]
    meta: Optional[dict]
    jsonapi: Optional[JsonAPI]
    links: Optional[Links]

class Info(BaseModel):
    """Information dict about the API"""
    meta: dict
    jsonapi: Optional[JsonAPI]
    links: Optional[Links]

att_pat_prop = constr(regex=r'^(?!relationships$|links$|id$|type$)\\w[-\\w_]*$')
class Attributes(BaseModel):
    """Members of the attributes object (\"attributes\") represent information about the resource object in which it's defined."""
    items: Optional[Dict[att_pat_prop, Any]]

class RelationshipLinks(BaseModel):
    """A resource object **MAY** contain references to other resource objects (\"relationships\"). Relationships may be to-one or to-many. Relationships can be specified by including a member in a resource's links object."""
    self: Optional[Link]
    related: Optional[Link]

class Linkage(BaseModel):
    """The \"type\" and \"id\" to non-empty members."""
    type: str
    id: str
    meta: Optional[dict]

class Relationship(BaseModel):
    """Representation of one reference from the resource object in which it's defined to other resource objects."""
    links: Optional[RelationshipLinks]
    data: Optional[Union[Linkage, Set[Linkage]]]
    meta: Optional[dict]

# class Empty(None):
#     """Describes an empty to-one relationship."""

class RelationshipToOne(Linkage):
    """References to other resource objects in a to-one (\"relationship\"). Relationships can be specified by including a member in a resource's links object."""

class RelationshipToMany(Set[Linkage]):
    """An array of objects each containing \"type\" and \"id\" members for to-many relationships."""

rel_pat_prop = constr(regex=r"^(?!id$|type$)\\w[-\\w_]*$")
class Relationships(BaseModel):
    """Members of the relationships object (\"relationships\") represent references from the resource object in which it's defined to other resource objects."""
    items : Optional[Dict[rel_pat_prop, Relationship]]

class Resource(BaseModel):
    """\"Resource objects\" appear in a JSON:API document to represent resources."""
    id: str
    type: str
    links: Optional[Links]
    meta: Optional[dict]
    attributes: Optional[Attributes]
    relationships: Optional[Relationships]

class Success(BaseModel):
    """A Successful response"""
    data: Union[None, Resource, Set[Resource]]
    included: Optional[Set[Resource]]
    meta: Optional[dict]
    links: Optional[Union[Links, Pagination]]
    jsonapi: Optional[JsonAPI]
