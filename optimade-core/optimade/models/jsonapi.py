"""This module should reproduce JSON API v1.0 https://jsonapi.org/format/1.0/"""
# pylint: disable=no-self-argument
from typing import Optional, Union, List
from pydantic import (  # pylint: disable=no-name-in-module
    BaseModel,
    AnyUrl,
    Field,
    root_validator,
)


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

    href: AnyUrl = Field(..., description="a string containing the link’s URL.")
    meta: Optional[Meta] = Field(
        None,
        description="a meta object containing non-standard meta-information about the link.",
    )


class JsonApi(BaseModel):
    """An object describing the server's implementation"""

    version: str = Field(default="1.0", description="Version of the json API used")
    meta: Optional[Meta] = Field(None, description="Non-standard meta information")


class ToplevelLinks(BaseModel):
    """A set of Links objects, possibly including pagination"""

    self: Optional[Union[AnyUrl, Link]] = Field(None, description="A link to itself")
    related: Optional[Union[AnyUrl, Link]] = Field(
        None, description="A related resource link"
    )

    # Pagination
    first: Optional[AnyUrl] = Field(None, description="The first page of data")
    last: Optional[AnyUrl] = Field(None, description="The last page of data")
    prev: Optional[AnyUrl] = Field(None, description="The previous page of data")
    next: Optional[AnyUrl] = Field(None, description="The next page of data")


class ErrorLinks(BaseModel):
    """A Links object specific to Error objects"""

    about: Optional[Union[AnyUrl, Link]] = Field(
        None,
        description="A link that leads to further details about this particular occurrence of the problem.",
    )


class ErrorSource(BaseModel):
    """an object containing references to the source of the error"""

    pointer: Optional[str] = Field(
        None,
        description="a JSON Pointer [RFC6901] to the associated entity in the request document "
        '[e.g. "/data" for a primary data object, or "/data/attributes/title" for a specific attribute].',
    )
    parameter: Optional[str] = Field(
        None,
        description="a string indicating which URI query parameter caused the error.",
    )


class Error(BaseModel):
    """An error response"""

    id: Optional[str] = Field(
        None,
        description="A unique identifier for this particular occurrence of the problem.",
    )
    links: Optional[ErrorLinks] = Field(
        None, description="A links object storing about"
    )
    status: Optional[str] = Field(
        None,
        description="the HTTP status code applicable to this problem, expressed as a string value.",
    )
    code: Optional[str] = Field(
        None,
        description="an application-specific error code, expressed as a string value.",
    )
    title: Optional[str] = Field(
        None,
        description="A short, human-readable summary of the problem. "
        "It **SHOULD NOT** change from occurrence to occurrence of the problem, except for purposes of localization.",
    )
    detail: Optional[str] = Field(
        None,
        description="A human-readable explanation specific to this occurrence of the problem.",
    )
    source: Optional[ErrorSource] = Field(
        None, description="An object containing references to the source of the error"
    )
    meta: Optional[Meta] = Field(
        None,
        description="a meta object containing non-standard meta-information about the error.",
    )

    def __hash__(self):
        return hash(self.json())


class BaseResource(BaseModel):
    """Minimum requirements to represent a Resource"""

    id: str = Field(..., description="Resource ID")
    type: str = Field(..., description="Resource type")


class RelationshipLinks(BaseModel):
    """A resource object **MAY** contain references to other resource objects (\"relationships\").
    Relationships may be to-one or to-many. Relationships can be specified by including a member in a resource's links object."""

    self: Optional[Union[AnyUrl, Link]] = Field(None, description="A link to itself")
    related: Optional[Union[AnyUrl, Link]] = Field(
        None, description="A related resource link"
    )

    @root_validator(pre=True)
    def either_self_or_related_must_be_specified(cls, values):
        for value in values.values():
            if value is not None:
                break
        else:
            raise ValueError(
                "Either 'self' or 'related' MUST be specified for RelationshipLinks"
            )
        return values


class Relationship(BaseModel):
    """Representation references from the resource object in which it’s defined to other resource objects."""

    links: Optional[RelationshipLinks] = Field(
        None,
        description="a links object containing at least one of the following: self, related",
    )
    data: Optional[Union[BaseResource, List[BaseResource]]] = Field(
        None, description="Resource linkage", uniqueItems=True
    )
    meta: Optional[Meta] = Field(
        None,
        description="a meta object that contains non-standard meta-information about the relationship.",
    )

    @root_validator(pre=True)
    def at_least_one_relationship_key_must_be_set(cls, values):
        for value in values.values():
            if value is not None:
                break
        else:
            raise ValueError(
                "Either 'links', 'data', or 'meta' MUST be specified for Relationship"
            )
        return values


class Relationships(BaseModel):
    """
    Members of the relationships object (\"relationships\") represent references from the resource object in which it's defined to other resource objects.
    Keys MUST NOT be:
        type
        id
    """

    @root_validator(pre=True)
    def check_illegal_relationships_fields(cls, values):
        illegal_fields = ("id", "type")
        for field in illegal_fields:
            if field in values:
                raise ValueError(
                    f"{illegal_fields} MUST NOT be fields under Relationships"
                )
        return values


class ResourceLinks(BaseModel):
    """A Resource Links object"""

    self: Optional[Union[AnyUrl, Link]] = Field(
        None,
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

    class Config:
        extra = "allow"

    @root_validator(pre=True)
    def check_illegal_attributes_fields(cls, values):
        illegal_fields = ("relationships", "links", "id", "type")
        for field in illegal_fields:
            if field in values:
                raise ValueError(
                    f"{illegal_fields} MUST NOT be fields under Attributes"
                )
        return values


class Resource(BaseResource):
    """Resource objects appear in a JSON:API document to represent resources."""

    links: Optional[ResourceLinks] = Field(
        None, description="a links object containing links related to the resource."
    )
    meta: Optional[Meta] = Field(
        None,
        description="a meta object containing non-standard meta-information about a resource that can not be represented as an attribute or relationship.",
    )
    attributes: Optional[Attributes] = Field(
        None,
        description="an attributes object representing some of the resource’s data.",
    )
    relationships: Optional[Relationships] = Field(
        None,
        description="a relationships object describing relationships between the resource and other JSON:API resources.",
    )


class Response(BaseModel):
    """A top-level response"""

    data: Optional[Union[None, Resource, List[Resource]]] = Field(
        None, description="Outputted Data", uniqueItems=True
    )
    meta: Optional[Meta] = Field(
        None,
        description="A meta object containing non-standard information related to the Success",
    )
    errors: Optional[List[Error]] = Field(
        None, description="A list of unique errors", uniqueItems=True
    )
    included: Optional[List[Resource]] = Field(
        None, description="A list of unique included resources", uniqueItems=True
    )
    links: Optional[ToplevelLinks] = Field(
        None, description="Links associated with the primary data or errors"
    )
    jsonapi: Optional[JsonApi] = Field(
        None, description="Information about the JSON API used"
    )

    @root_validator(pre=True)
    def either_data_meta_or_errors_must_be_set(cls, values):
        required_fields = ("data", "meta", "errors")
        if not any(values.get(field) for field in required_fields):
            raise ValueError(
                f"At least one of {required_fields} MUST be specified in the top-level response"
            )
        return values
