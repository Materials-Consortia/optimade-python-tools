"""This module should reproduce JSON API v1.0 https://jsonapi.org/format/1.0/"""
# pylint: disable=no-name-in-module,no-self-argument
from typing import Optional, Set, Union, Any, List
from pydantic import BaseModel, AnyUrl, Schema, validator


__all__ = (
    "Meta",
    "Link",
    "JsonApi",
    "ToplevelLinks",
    "ErrorLinks",
    "ErrorSource",
    "BaseResource",
    "RelationshipLinks",
    "Relationship",
    "Relationships",
    "ResourceLinks",
    "Attributes",
    "Resource",
    "Response",
)


class Meta(BaseModel):
    """Non-standard meta-information that can not be represented as an attribute or relationship."""

    class Config:
        extra = "allow"


class Link(BaseModel):
    """A link **MUST** be represented as either: a string containing the link's URL or a link object."""

    href: AnyUrl = Schema(..., description="a string containing the link’s URL.")
    meta: Optional[Meta] = Schema(
        ...,
        description="a meta object containing non-standard meta-information about the link.",
    )


class JsonApi(BaseModel):
    """An object describing the server's implementation"""

    version: str = Schema(..., description="Version of the json API used")
    meta: Optional[Meta] = Schema(..., description="Non-standard meta information")


class ToplevelLinks(BaseModel):
    """A set of Links objects, possibly including pagination"""

    self: Optional[Union[AnyUrl, Link]] = Schema(..., description="A link to itself")
    related: Optional[Union[AnyUrl, Link]] = Schema(
        ..., description="A related resource link"
    )

    # Pagination
    first: Optional[AnyUrl] = Schema(..., description="The first page of data")
    last: Optional[AnyUrl] = Schema(..., description="The last page of data")
    prev: Optional[AnyUrl] = Schema(..., description="The previous page of data")
    next: Optional[AnyUrl] = Schema(..., description="The next page of data")


class ErrorLinks(BaseModel):
    """A Links object specific to Error objects"""

    about: Optional[Union[AnyUrl, Link]] = Schema(
        ...,
        description="A link that leads to further details about this particular occurrence of the problem.",
    )


class ErrorSource(BaseModel):
    """an object containing references to the source of the error"""

    pointer: Optional[str] = Schema(
        ...,
        description="a JSON Pointer [RFC6901] to the associated entity in the request document "
        '[e.g. "/data" for a primary data object, or "/data/attributes/title" for a specific attribute].',
    )
    parameter: Optional[str] = Schema(
        ...,
        description="a string indicating which URI query parameter caused the error.",
    )


class Error(BaseModel):
    """An error response"""

    id: Optional[str] = Schema(
        ...,
        description="A unique identifier for this particular occurrence of the problem.",
    )
    links: Optional[ErrorLinks] = Schema(
        ..., description="A links object storing about"
    )
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
        description="A short, human-readable summary of the problem. "
        "It **SHOULD NOT** change from occurrence to occurrence of the problem, except for purposes of localization.",
    )
    detail: Optional[str] = Schema(
        ...,
        description="A human-readable explanation specific to this occurrence of the problem.",
    )
    source: Optional[ErrorSource] = Schema(
        ..., description="An object containing references to the source of the error"
    )
    meta: Optional[Meta] = Schema(
        ...,
        description="a meta object containing non-standard meta-information about the error.",
    )


class BaseResource(BaseModel):
    """Minimum requirements to represent a Resource"""

    id: str = Schema(..., description="Resource ID")
    type: str = Schema(..., description="Resource type")


class RelationshipLinks(BaseModel):
    """A resource object **MAY** contain references to other resource objects (\"relationships\").
    Relationships may be to-one or to-many. Relationships can be specified by including a member in a resource's links object."""

    self: Optional[Union[AnyUrl, Link]] = Schema(..., description="A link to itself")
    related: Optional[Union[AnyUrl, Link]] = Schema(
        ..., description="A related resource link"
    )

    @validator("related", always=True)
    def either_self_or_related_must_be_specified(cls, v, values):
        if values.get("self", None) is None and v is None:
            raise ValueError(
                "Either 'self' or 'related' MUST be specified for RelationshipLinks"
            )
        return v


class Relationship(BaseModel):
    """Representation references from the resource object in which it’s defined to other resource objects."""

    links: Optional[RelationshipLinks] = Schema(
        ...,
        description="a links object containing at least one of the following: self, related",
    )
    data: Optional[Union[BaseResource, List[BaseResource]]] = Schema(
        ..., description="Resource linkage"
    )
    meta: Optional[Meta] = Schema(
        ...,
        description="a meta object that contains non-standard meta-information about the relationship.",
    )

    @validator("meta", always=True)
    def at_least_one_relationship_key_must_be_set(cls, v, values):
        if (
            values.get("links", None) is None
            and values.get("data", None) is None
            and v is None
        ):
            raise ValueError(
                "Either 'links', 'data', or 'meta' MUST be specified for relationship"
            )
        return v


class Relationships(BaseModel):
    """
    Members of the relationships object (\"relationships\") represent references from the resource object in which it's defined to other resource objects.
    Keys MUST NOT be:
        type
        id
    """

    id: Optional[Any] = Schema(..., description="Not allowed key")
    type: Optional[Any] = Schema(..., description="Not allowed key")

    @validator("id", "type")
    def check_illegal_relationships_fields(cls, v):
        raise ValueError('"id", "type" MUST NOT be fields under relationships')


class ResourceLinks(BaseModel):
    """A Resource Links object"""

    self: Optional[Union[AnyUrl, Link]] = Schema(
        ...,
        description="A link that identifies the resource represented by the resource object.",
    )


class Attributes(BaseModel):
    """
    Members of the attributes object ("attributes\") represent information about the resource object in which it's defined.
    The keys for Attributes MUST NOT be:
        relationships
        links
        id
        type
    """

    relationships: Optional[Any] = Schema(..., description="Not allowed key")
    links: Optional[Any] = Schema(..., description="Not allowed key")
    id: Optional[Any] = Schema(..., description="Not allowed key")
    type: Optional[Any] = Schema(..., description="Not allowed key")

    class Config:
        extra = "allow"

    @validator("relationships", "links", "id", "type")
    def check_illegal_attributes_fields(cls, v):
        raise ValueError(
            '"relationships", "links", "id", "type" MUST NOT be fields under attributes'
        )


class Resource(BaseResource):
    """Resource objects appear in a JSON:API document to represent resources."""

    links: Optional[ResourceLinks] = Schema(
        ..., description="a links object containing links related to the resource."
    )
    meta: Optional[Meta] = Schema(
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


class Response(BaseModel):
    """A top-level response"""

    data: Optional[Union[None, Resource, Set[Resource]]] = Schema(
        ..., description="Outputted Data"
    )
    meta: Optional[Meta] = Schema(
        ...,
        description="A meta object containing non-standard information related to the Success",
    )
    errors: Optional[Set[Error]] = Schema(..., description="A list of errors")
    included: Optional[Set[Resource]] = Schema(
        ..., description="A list of resources that are included"
    )
    links: Optional[ToplevelLinks] = Schema(
        ..., description="Links associated with the failure"
    )
    jsonapi: Optional[JsonApi] = Schema(
        ..., description="Information about the JSON API used"
    )

    @validator("errors", always=True)
    def either_data_meta_or_errors_must_be_set(cls, v, values):
        if (
            values.get("data", None) is None
            and values.get("meta", None) is None
            and v is None
        ):
            raise ValueError(
                "Either 'data', 'meta', or 'errors' must be specified in the top-level response"
            )
        return v
