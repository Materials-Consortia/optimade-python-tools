"""
This module should reproduce https://jsonapi.org/schema
"""
from typing import Optional, Set, Union, Dict, Any
from pydantic import BaseModel, UrlStr, constr, Schema


class Meta(Dict[str, Any]):
    """Non-standard meta-information that can not be represented as an attribute or relationship."""


class Link(BaseModel):
    """A link **MUST** be represented as either: a string containing the link's URL or a link object."""

    href: UrlStr = Schema(..., description="a string containing the link’s URL.")
    meta: Optional[dict] = Schema(
        ...,
        description="a meta object containing non-standard meta-information about the link.",
    )


class Links(BaseModel):
    """A Links object is a set of keys with a Link value"""

    next: Optional[Union[UrlStr, Link]] = Schema(
        ..., description="A Link to the next object"
    )
    self: Optional[Union[UrlStr, Link]] = Schema(..., description="A link to itself")
    related: Optional[Union[UrlStr, Link]] = Schema(
        ..., description="A related resource link"
    )
    about: Optional[Union[UrlStr, Link]] = Schema(
        ...,
        description="a link that leads to further details about this particular occurrence of the problem.",
    )


class JsonAPI(BaseModel):
    """An object describing the server's implementation"""

    version: str = Schema(..., description="Version of the json API used")
    meta: Optional[dict] = Schema(..., description="Non-standard meta information")


class Pagination(BaseModel):
    """
    A set of urls to different pages:
    """

    first: Optional[UrlStr] = Schema(..., description="The first page of data")
    last: Optional[UrlStr] = Schema(..., description="The last page of data")
    prev: Optional[UrlStr] = Schema(..., description="The previous page of data")
    next: Optional[UrlStr] = Schema(..., description="The next page of data")


class Source(BaseModel):
    """an object containing references to the source of the error"""

    pointer: Optional[str] = Schema(
        ...,
        description='a JSON Pointer [RFC6901] to the associated entity in the request document [e.g. "/data" for a primary data object, or "/data/attributes/title" for a specific attribute].',
    )
    parmeter: Optional[str] = Schema(
        ...,
        description="a string indicating which URI query parameter caused the error.",
    )


class Error(BaseModel):
    """
    An error response
    """

    id: Optional[str] = Schema(
        ...,
        description="A unique identifier for this particular occurrence of the problem.",
    )
    links: Optional[Links] = Schema(..., description="A links object storing about")
    status: Optional[str] = Schema(
        ...,
        description="the HTTP status code applicable to this problem, expressed as a string value.",
    )
    code: Optional[str] = Schema(
        ...,
        description="an application-specific error code, expressed as a string value.",
    )
    title: Optional[str] = Schema(
        ...,
        description="A short, human-readable summary of the problem. It **SHOULD NOT** change from occurrence to occurrence of the problem, except for purposes of localization.",
    )
    detail: Optional[str] = Schema(
        ...,
        description="A human-readable explanation specific to this occurrence of the problem.",
    )
    source: Optional[Source] = Schema(
        ..., description="An object containing references to the source of the error"
    )
    meta: Optional[dict] = Schema(
        ...,
        description="a meta object containing non-standard meta-information about the error.",
    )


class Warning(Error):
    """ OPTiMaDe-specific warning class based on jsonapi.Error. From the
    specification:

        A warning resource object is defined similarly to a JSON API
        error object, but MUST also include the field type, which MUST
        have the value "warning". The field detail MUST be present and
        SHOULD contain a non-critical message, e.g., reporting
        unrecognized search attributes or deprecated features.

    """

    type: str = Schema("warning", const=True)


class Failure(BaseModel):
    """A failure object"""

    errors: Set[Error] = Schema(..., description="A list of errors")
    meta: Optional[dict] = Schema(
        ...,
        description="a meta object containing non-standard meta-information about the failure.",
    )
    jsonapi: Optional[JsonAPI] = Schema(
        ..., description="Information about the JSON API used"
    )
    links: Optional[Links] = Schema(
        ..., description="Links associated with the failure"
    )


class Info(BaseModel):
    """Information dict about the API"""

    meta: dict = Schema(
        ...,
        description="a meta object containing non-standard meta-information about the failure.",
    )
    jsonapi: Optional[JsonAPI] = Schema(
        ..., description="Information about the JSON API used"
    )
    links: Optional[Links] = Schema(
        ..., description="Links associated with the failure"
    )


att_pat_prop = constr(regex=r"^(?!relationships$|links$|id$|type$)\\w[-\\w_]*$")


class Attributes(Dict[str, Any]):
    """
    Members of the attributes object ("attributes\") represent information about the resource object in which it's defined.
    The keys for Attributes must NOT be:
        relationships
        links
        id
        type
    """


class RelationshipLinks(BaseModel):
    """A resource object **MAY** contain references to other resource objects (\"relationships\"). Relationships may be to-one or to-many. Relationships can be specified by including a member in a resource's links object."""

    self: Optional[Link] = Schema(..., description="A link to itself")
    related: Optional[Link] = Schema(..., description="A related resource link")


class Linkage(BaseModel):
    """The \"type\" and \"id\" to non-empty members."""

    type: str = Schema(..., description="The type of linkage")
    id: str = Schema(..., description="The id of the linkage")
    meta: Optional[dict] = Schema(
        ..., description="The non-standard meta-information about the linkage"
    )


class Relationship(BaseModel):
    """Representation references from the resource object in which it’s defined to other resource objects."""

    links: Optional[RelationshipLinks] = Schema(
        ...,
        description="a links object containing at least one of the following: self, related",
    )
    data: Optional[Union[Linkage, Set[Linkage]]] = Schema(
        ..., description="Resource linkage"
    )
    meta: Optional[dict] = Schema(
        ...,
        description="a meta object that contains non-standard meta-information about the relationship.",
    )


# class Empty(None):
#     """Describes an empty to-one relationship."""


class RelationshipToOne(Linkage):
    """References to other resource objects in a to-one (\"relationship\"). Relationships can be specified by including a member in a resource's links object."""


class RelationshipToMany(Set[Linkage]):
    """An array of objects each containing \"type\" and \"id\" members for to-many relationships."""


rel_pat_prop = constr(regex=r"^(?!id$|type$)\\w[-\\w_]*$")


class Relationships(Dict[str, Relationship]):
    """
    Members of the relationships object (\"relationships\") represent references from the resource object in which it's defined to other resource objects.
    Keys MUST NOT be:
        type
        id
    """


class Resource(BaseModel):
    """Resource objects appear in a JSON:API document to represent resources."""

    id: str = Schema(..., description="Resource ID")
    type: str = Schema(..., description="Resource type")
    links: Optional[Links] = Schema(
        ..., description="a links object containing links related to the resource."
    )
    meta: Optional[dict] = Schema(
        ...,
        description="a meta object containing non-standard meta-information about a resource that can not be represented as an attribute or relationship.",
    )
    attributes: Optional[Attributes] = Schema(
        ...,
        description="an attributes object representing some of the resource’s data.",
    )
    relationships: Optional[Relationships] = Schema(
        ...,
        description="a relationships object describing relationships between the resource and other JSON:API resources.",
    )


class Success(BaseModel):
    """A Successful response"""

    data: Union[None, Resource, Set[Resource]] = Schema(
        ..., description="Outputted Data"
    )
    included: Optional[Set[Resource]] = Schema(
        ..., description="A list of resources that are included"
    )
    meta: Optional[dict] = Schema(
        ...,
        description="A meta object containing non-standard information related to the Success",
    )
    links: Optional[Union[Links, Pagination]] = Schema(
        ..., description="Information about the JSON API used"
    )
    jsonapi: Optional[JsonAPI] = Schema(
        ..., description="Links associated with the failure"
    )
