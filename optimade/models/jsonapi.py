"""This module should reproduce JSON API v1.0 https://jsonapi.org/format/1.0/"""

from datetime import datetime, timezone
from typing import Annotated, Any, Optional, Union

from pydantic import (
    AnyUrl,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    TypeAdapter,
    model_validator,
)

from optimade.models.utils import StrictField

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

    model_config = ConfigDict(extra="allow")


class Link(BaseModel):
    """A link **MUST** be represented as either: a string containing the link's URL or a link object."""

    href: Annotated[
        AnyUrl, StrictField(description="a string containing the link's URL.")
    ]
    meta: Annotated[
        Optional[Meta],
        StrictField(
            description="a meta object containing non-standard meta-information about the link.",
        ),
    ] = None


JsonLinkType = Union[AnyUrl, Link]


class JsonApi(BaseModel):
    """An object describing the server's implementation"""

    version: Annotated[str, StrictField(description="Version of the json API used")] = (
        "1.0"
    )
    meta: Annotated[
        Optional[Meta], StrictField(description="Non-standard meta information")
    ] = None


class ToplevelLinks(BaseModel):
    """A set of Links objects, possibly including pagination"""

    model_config = ConfigDict(extra="allow")

    self: Annotated[
        Optional[JsonLinkType], StrictField(description="A link to itself")
    ] = None
    related: Annotated[
        Optional[JsonLinkType], StrictField(description="A related resource link")
    ] = None

    # Pagination
    first: Annotated[
        Optional[JsonLinkType], StrictField(description="The first page of data")
    ] = None
    last: Annotated[
        Optional[JsonLinkType], StrictField(description="The last page of data")
    ] = None
    prev: Annotated[
        Optional[JsonLinkType], StrictField(description="The previous page of data")
    ] = None
    next: Annotated[
        Optional[JsonLinkType], StrictField(description="The next page of data")
    ] = None

    @model_validator(mode="after")
    def check_additional_keys_are_links(self) -> "ToplevelLinks":
        """The `ToplevelLinks` class allows any additional keys, as long as
        they are also Links or Urls themselves.

        """
        for field, value in self:
            if field not in self.model_fields:
                setattr(
                    self,
                    field,
                    TypeAdapter(Optional[JsonLinkType]).validate_python(value),
                )

        return self


class ErrorLinks(BaseModel):
    """A Links object specific to Error objects"""

    about: Annotated[
        Optional[JsonLinkType],
        StrictField(
            description="A link that leads to further details about this particular occurrence of the problem.",
        ),
    ] = None


class ErrorSource(BaseModel):
    """an object containing references to the source of the error"""

    pointer: Annotated[
        Optional[str],
        StrictField(
            description="a JSON Pointer [RFC6901] to the associated entity in the request document "
            '[e.g. "/data" for a primary data object, or "/data/attributes/title" for a specific attribute].',
        ),
    ] = None
    parameter: Annotated[
        Optional[str],
        StrictField(
            description="a string indicating which URI query parameter caused the error.",
        ),
    ] = None


class Error(BaseModel):
    """An error response"""

    id: Annotated[
        Optional[str],
        StrictField(
            description="A unique identifier for this particular occurrence of the problem.",
        ),
    ] = None
    links: Annotated[
        Optional[ErrorLinks], StrictField(description="A links object storing about")
    ] = None
    status: Annotated[
        Optional[Annotated[str, BeforeValidator(str)]],
        StrictField(
            description="the HTTP status code applicable to this problem, expressed as a string value.",
        ),
    ] = None
    code: Annotated[
        Optional[str],
        StrictField(
            description="an application-specific error code, expressed as a string value.",
        ),
    ] = None
    title: Annotated[
        Optional[str],
        StrictField(
            description="A short, human-readable summary of the problem. "
            "It **SHOULD NOT** change from occurrence to occurrence of the problem, except for purposes of localization.",
        ),
    ] = None
    detail: Annotated[
        Optional[str],
        StrictField(
            description="A human-readable explanation specific to this occurrence of the problem.",
        ),
    ] = None
    source: Annotated[
        Optional[ErrorSource],
        StrictField(
            description="An object containing references to the source of the error"
        ),
    ] = None
    meta: Annotated[
        Optional[Meta],
        StrictField(
            description="a meta object containing non-standard meta-information about the error.",
        ),
    ] = None

    def __hash__(self):
        return hash(self.model_dump_json())


def resource_json_schema_extra(
    schema: dict[str, Any], model: type["BaseResource"]
) -> None:
    """Ensure `id` and `type` are the first two entries in the list required properties.

    Note:
        This _requires_ that `id` and `type` are the _first_ model fields defined
        for all sub-models of `BaseResource`.

    """
    if "id" not in schema.get("required", []):
        schema["required"] = ["id"] + schema.get("required", [])
    if "type" not in schema.get("required", []):
        required = []
        for field in schema.get("required", []):
            required.append(field)
            if field == "id":
                # To make sure the property order match the listed properties,
                # this ensures "type" is added immediately after "id".
                required.append("type")
        schema["required"] = required


class BaseResource(BaseModel):
    """Minimum requirements to represent a Resource"""

    model_config = ConfigDict(json_schema_extra=resource_json_schema_extra)

    id: Annotated[str, StrictField(description="Resource ID")]
    type: Annotated[str, StrictField(description="Resource type")]


class RelationshipLinks(BaseModel):
    """A resource object **MAY** contain references to other resource objects ("relationships").
    Relationships may be to-one or to-many.
    Relationships can be specified by including a member in a resource's links object.

    """

    self: Annotated[
        Optional[JsonLinkType],
        StrictField(
            description="""A link for the relationship itself (a 'relationship link').
This link allows the client to directly manipulate the relationship.
When fetched successfully, this link returns the [linkage](https://jsonapi.org/format/1.0/#document-resource-object-linkage) for the related resources as its primary data.
(See [Fetching Relationships](https://jsonapi.org/format/1.0/#fetching-relationships).)""",
        ),
    ] = None
    related: Annotated[
        Optional[JsonLinkType],
        StrictField(
            description="A [related resource link](https://jsonapi.org/format/1.0/#document-resource-object-related-resource-links).",
        ),
    ] = None

    @model_validator(mode="after")
    def either_self_or_related_must_be_specified(self) -> "RelationshipLinks":
        if self.self is None and self.related is None:
            raise ValueError(
                "Either 'self' or 'related' MUST be specified for RelationshipLinks"
            )
        return self


class Relationship(BaseModel):
    """Representation references from the resource object in which it's defined to other resource objects."""

    links: Annotated[
        Optional[RelationshipLinks],
        StrictField(
            description="a links object containing at least one of the following: self, related",
        ),
    ] = None
    data: Annotated[
        Optional[Union[BaseResource, list[BaseResource]]],
        StrictField(description="Resource linkage"),
    ] = None
    meta: Annotated[
        Optional[Meta],
        StrictField(
            description="a meta object that contains non-standard meta-information about the relationship.",
        ),
    ] = None

    @model_validator(mode="after")
    def at_least_one_relationship_key_must_be_set(self) -> "Relationship":
        if self.links is None and self.data is None and self.meta is None:
            raise ValueError(
                "Either 'links', 'data', or 'meta' MUST be specified for Relationship"
            )
        return self


class Relationships(BaseModel):
    """
    Members of the relationships object (\"relationships\") represent references from the resource object in which it's defined to other resource objects.
    Keys MUST NOT be:
        type
        id
    """

    @model_validator(mode="after")
    def check_illegal_relationships_fields(self) -> "Relationships":
        illegal_fields = ("id", "type")
        for field in illegal_fields:
            if hasattr(self, field):
                raise ValueError(
                    f"{illegal_fields} MUST NOT be fields under Relationships"
                )
        return self


class ResourceLinks(BaseModel):
    """A Resource Links object"""

    self: Annotated[
        Optional[JsonLinkType],
        StrictField(
            description="A link that identifies the resource represented by the resource object.",
        ),
    ] = None


class Attributes(BaseModel):
    """
    Members of the attributes object ("attributes\") represent information about the resource object in which it's defined.
    The keys for Attributes MUST NOT be:
        relationships
        links
        id
        type
    """

    model_config = ConfigDict(extra="allow")

    @model_validator(mode="after")
    def check_illegal_attributes_fields(self) -> "Attributes":
        illegal_fields = ("relationships", "links", "id", "type")
        for field in illegal_fields:
            if hasattr(self, field):
                raise ValueError(
                    f"{illegal_fields} MUST NOT be fields under Attributes"
                )
        return self


class Resource(BaseResource):
    """Resource objects appear in a JSON API document to represent resources."""

    links: Annotated[
        Optional[ResourceLinks],
        StrictField(
            description="a links object containing links related to the resource."
        ),
    ] = None
    meta: Annotated[
        Optional[Meta],
        StrictField(
            description="a meta object containing non-standard meta-information about a resource that can not be represented as an attribute or relationship.",
        ),
    ] = None
    attributes: Annotated[
        Optional[Attributes],
        StrictField(
            description="an attributes object representing some of the resource’s data.",
        ),
    ] = None
    relationships: Annotated[
        Optional[Relationships],
        StrictField(
            description="""[Relationships object](https://jsonapi.org/format/1.0/#document-resource-object-relationships)
describing relationships between the resource and other JSON API resources.""",
        ),
    ] = None


class Response(BaseModel):
    """A top-level response."""

    data: Annotated[
        Optional[Union[None, Resource, list[Resource]]],
        StrictField(description="Outputted Data", uniqueItems=True),
    ] = None
    meta: Annotated[
        Optional[Meta],
        StrictField(
            description="A meta object containing non-standard information related to the Success",
        ),
    ] = None
    errors: Annotated[
        Optional[list[Error]],
        StrictField(description="A list of unique errors", uniqueItems=True),
    ] = None
    included: Annotated[
        Optional[list[Resource]],
        StrictField(
            description="A list of unique included resources", uniqueItems=True
        ),
    ] = None
    links: Annotated[
        Optional[ToplevelLinks],
        StrictField(description="Links associated with the primary data or errors"),
    ] = None
    jsonapi: Annotated[
        Optional[JsonApi],
        StrictField(description="Information about the JSON API used"),
    ] = None

    @model_validator(mode="after")
    def either_data_meta_or_errors_must_be_set(self) -> "Response":
        required_fields = ("data", "meta", "errors")
        if not any(field in self.model_fields_set for field in required_fields):
            raise ValueError(
                f"At least one of {required_fields} MUST be specified in the top-level response"
            )
        if "errors" in self.model_fields_set and not self.errors:
            raise ValueError("Errors MUST NOT be an empty or 'null' value.")
        return self

    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.astimezone(timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )
        }
    )
    """The specification mandates that datetimes must be encoded following
    [RFC3339](https://tools.ietf.org/html/rfc3339), which does not support
    fractional seconds, thus they must be stripped in the response. This can
    cause issues when the underlying database contains fields that do include
    microseconds, as filters may return unexpected results.
    """
