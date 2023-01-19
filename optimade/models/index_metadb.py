# pylint: disable=no-self-argument
from enum import Enum
from typing import Dict, Union

from pydantic import BaseModel, Field  # pylint: disable=no-name-in-module

from optimade.models.baseinfo import BaseInfoAttributes, BaseInfoResource
from optimade.models.jsonapi import BaseResource
from optimade.models.utils import StrictField

__all__ = (
    "IndexInfoAttributes",
    "RelatedLinksResource",
    "IndexRelationship",
    "IndexInfoResource",
)


class DefaultRelationship(Enum):
    """Enumeration of key(s) for relationship dictionary in IndexInfoResource"""

    DEFAULT = "default"


class IndexInfoAttributes(BaseInfoAttributes):
    """Attributes for Base URL Info endpoint for an Index Meta-Database"""

    is_index: bool = StrictField(
        True,
        description="This must be `true` since this is an index meta-database (see section Index Meta-Database).",
    )


class RelatedLinksResource(BaseResource):
    """A related Links resource object"""

    type: str = Field("links", regex="^links$")


class IndexRelationship(BaseModel):
    """Index Meta-Database relationship"""

    data: Union[None, RelatedLinksResource] = StrictField(
        ...,
        description="""[JSON API resource linkage](http://jsonapi.org/format/1.0/#document-links).
It MUST be either `null` or contain a single Links identifier object with the fields `id` and `type`""",
    )


class IndexInfoResource(BaseInfoResource):
    """Index Meta-Database Base URL Info endpoint resource"""

    attributes: IndexInfoAttributes = Field(...)
    relationships: Union[
        None, Dict[DefaultRelationship, IndexRelationship]
    ] = StrictField(  # type: ignore[assignment]
        ...,
        title="Relationships",
        description="""Reference to the Links identifier object under the `links` endpoint that the provider has chosen as their 'default' OPTIMADE API database.
A client SHOULD present this database as the first choice when an end-user chooses this provider.""",
    )
