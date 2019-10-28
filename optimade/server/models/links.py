from pydantic import Schema, UrlStr, validator
from typing import Union

from .jsonapi import Link
from .entries import EntryResourceAttributes, EntryResource


class LinksResourceAttributes(EntryResourceAttributes):
    """Links endpoint resource object attributes"""

    name: str = Schema(
        ...,
        description="Human-readable name for the OPTiMaDe API implementation "
        "a client may provide in a list to an end-user.",
    )
    description: str = Schema(
        ...,
        description="Human-readable description for the OPTiMaDe API implementation "
        "a client may provide in a list to an end-user.",
    )
    base_url: Union[UrlStr, Link] = Schema(
        ...,
        description="JSON API links object, pointing to the base URL for this implementation",
    )


class LinksResource(EntryResource):
    """A Links endpoint resource object"""

    type: str = Schema(
        ...,
        description='MUST be either "parent", "child", or "provider". '
        "These objects are described in detail in sections Parent and Child Objects "
        "and Provider Objects.",
    )

    attributes: LinksResourceAttributes

    @validator("type")
    def type_must_be_in_specific_set(cls, value):
        if value not in {"parent", "child", "provider"}:
            raise AssertionError(
                "name of Links endpoint resource MUST be either 'parent, 'child', or 'provider'"
            )
        return value


class ChildResource(LinksResource):
    """A child object representing a link to an implementation exactly one layer below the current implementation"""

    type = Schema("child", const=True)


class ParentResource(LinksResource):
    """A parent object representing a link to an implementation exactly one layer above the current implementation"""

    type = Schema("parent", const=True)


class ProviderResource(LinksResource):
    """A provider object representing a link to another index meta-database by another database provider"""

    type = Schema("provider", const=True)
