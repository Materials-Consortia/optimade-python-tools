from typing import Annotated, Literal

from pydantic import BaseModel

from optimade.models.baseinfo import BaseInfoAttributes, BaseInfoResource
from optimade.models.jsonapi import BaseResource
from optimade.models.utils import StrictField

__all__ = (
    "IndexInfoAttributes",
    "RelatedLinksResource",
    "IndexRelationship",
    "IndexInfoResource",
)


class IndexInfoAttributes(BaseInfoAttributes):
    """Attributes for Base URL Info endpoint for an Index Meta-Database"""

    is_index: Annotated[
        bool,
        StrictField(
            description="This must be `true` since this is an index meta-database (see section Index Meta-Database).",
        ),
    ] = True


class RelatedLinksResource(BaseResource):
    """A related Links resource object"""

    type: Literal["links"] = "links"


class IndexRelationship(BaseModel):
    """Index Meta-Database relationship"""

    data: Annotated[
        RelatedLinksResource | None,
        StrictField(
            description="""[JSON API resource linkage](http://jsonapi.org/format/1.0/#document-links).
It MUST be either `null` or contain a single Links identifier object with the fields `id` and `type`""",
        ),
    ]


class IndexInfoResource(BaseInfoResource):
    """Index Meta-Database Base URL Info endpoint resource"""

    attributes: IndexInfoAttributes
    relationships: Annotated[  # type: ignore[assignment]
        dict[Literal["default"], IndexRelationship] | None,
        StrictField(
            title="Relationships",
            description="""Reference to the Links identifier object under the `links` endpoint that the provider has chosen as their 'default' OPTIMADE API database.
A client SHOULD present this database as the first choice when an end-user chooses this provider.""",
        ),
    ]
