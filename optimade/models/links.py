# pylint: disable=no-self-argument
from pydantic import (  # pylint: disable=no-name-in-module
    Field,
    AnyUrl,
    validator,
    root_validator,
)
from typing import Union

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

    @validator("link_type")
    def link_type_must_be_in_specific_set(cls, value):
        if value not in {"child", "root", "external", "providers"}:
            raise ValueError(
                "link_type MUST be either 'child, 'root', 'external', or 'providers'"
            )
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
