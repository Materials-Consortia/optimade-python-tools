# pylint: disable=no-self-argument
from pydantic import (  # pylint: disable=no-name-in-module
    Field,
    AnyUrl,
    validator,
    root_validator,
)
from typing import Union, Optional

from .jsonapi import Link, Attributes
from .entries import EntryResource


__all__ = (
    "LinksResourceAttributes",
    "LinksResource",
)


class LinksResourceAttributes(Attributes):
    """Links endpoint resource object attributes"""

    name: str = Field(
        ...,
        description="Human-readable name for the OPTIMADE API implementation "
        "a client may provide in a list to an end-user.",
    )
    description: str = Field(
        ...,
        description="Human-readable description for the OPTIMADE API implementation "
        "a client may provide in a list to an end-user.",
    )
    base_url: Union[AnyUrl, Link, None] = Field(
        ...,
        description="JSON API links object, pointing to the base URL for this implementation",
    )

    homepage: Union[AnyUrl, Link, None] = Field(
        ...,
        description="JSON API links object, pointing to a homepage URL for this implementation",
    )

    link_type: str = Field(
        ...,
        description="The link type of the represented resource in relation to this implementation. MUST be one of these values: 'child', 'root', 'external', 'providers'.",
    )

    aggregate: Optional[str] = Field(
        "ok",
        description="""A string indicating whether a client that is following links to aggregate results from different OPTIMADE implementations should follow this link or not.
This flag SHOULD NOT be indicated for links where :property:`link_type` is not :val:`child`.

If not specified, clients MAY assume that the value is :val:`ok`.
If specified, and the value is anything different than :val:`ok`, the client MUST assume that the server is suggesting not to follow the link during aggregation by default (also if the value is not among the known ones, in case a future specification adds new accepted values).

Specific values indicate the reason why the server is providing the suggestion.
A client MAY follow the link anyway if it has reason to do so (e.g., if the client is looking for all test databases, it MAY follow the links marked with :property:`aggregate`=:val:`test`).

If specified, it MUST be one of the values listed in section Link Aggregate Options.""",
    )

    no_aggregate_reason: Optional[str] = Field(
        None,
        description="""An OPTIONAL human-readable string indicating the reason for suggesting not to aggregate results following the link.
It SHOULD NOT be present if :property:`aggregate`=:val:`ok`.""",
    )

    @validator("link_type")
    def link_type_must_be_in_specific_set(cls, value):
        if value not in {"child", "root", "external", "providers"}:
            raise ValueError(
                "link_type MUST be either 'child, 'root', 'external', or 'providers'"
            )
        return value

    @validator("aggregate")
    def aggregate_must_be_in_specific_set(cls, value):
        if value is not None and value not in {"ok", "test", "staging", "no"}:
            raise ValueError("aggregate MUST be either 'ok, 'test', 'staging', or 'no'")
        return value


class LinksResource(EntryResource):
    """A Links endpoint resource object"""

    type: str = Field(
        "links",
        const=True,
        description="These objects are described in detail in the section Links Endpoint",
    )

    attributes: LinksResourceAttributes = Field(
        ...,
        description="a dictionary containing key-value pairs representing the "
        "entry's properties.",
    )

    @root_validator(pre=True)
    def relationships_must_not_be_present(cls, values):
        if values.get("relationships", None) is not None:
            raise ValueError('"relationships" is not allowed for links resources')
        return values
