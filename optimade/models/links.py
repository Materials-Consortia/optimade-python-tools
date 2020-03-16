# pylint: disable=no-self-argument
from pydantic import Field, AnyUrl, validator, root_validator
from typing import Union

from .jsonapi import Link, Attributes
from .entries import EntryResource


__all__ = (
    "LinksResourceAttributes",
    "LinksResource",
    "ChildResource",
    "ParentResource",
    "ProviderResource",
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


class LinksResource(EntryResource):
    """A Links endpoint resource object"""

    type: str = Field(
        ...,
        description='MUST be either "parent", "child", or "provider". '
        "These objects are described in detail in sections Parent and Child Objects "
        "and Provider Objects.",
    )

    attributes: LinksResourceAttributes = Field(
        ...,
        description="a dictionary containing key-value pairs representing the "
        "entry's properties.",
    )

    @validator("type")
    def type_must_be_in_specific_set(cls, value):
        if value not in {"parent", "child", "provider"}:
            raise ValueError(
                "name of Links endpoint resource MUST be either 'parent, 'child', or 'provider'"
            )
        return value

    @root_validator(pre=True)
    def relationships_must_not_be_present(cls, values):
        if values.get("relationships", None) is not None:
            raise ValueError('"relationships" is not allowed for links resources')
        return values


class ChildResource(LinksResource):
    """A child object representing a link to an implementation exactly one layer below the current implementation"""

    type: str = Field("child", const=True)


class ParentResource(LinksResource):
    """A parent object representing a link to an implementation exactly one layer above the current implementation"""

    type: str = Field("parent", const=True)


class ProviderResource(LinksResource):
    """A provider object representing a link to another index meta-database by another database provider"""

    type: str = Field("provider", const=True)
