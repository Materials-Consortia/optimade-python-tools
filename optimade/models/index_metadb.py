from pydantic import Field, BaseModel
from typing import Union, Dict

from .jsonapi import BaseResource
from .baseinfo import BaseInfoAttributes, BaseInfoResource


__all__ = (
    "IndexInfoAttributes",
    "RelatedChildResource",
    "IndexRelationship",
    "IndexInfoResource",
)


class IndexInfoAttributes(BaseInfoAttributes):
    """Attributes for Base URL Info endpoint for an Index Meta-Database"""

    is_index: bool = Field(
        default=True,
        const=True,
        description="If true, this is an index meta-database base URL (see section Index Meta-Database). "
        "If this member is not provided, the client MUST assume this is not an index meta-database base URL "
        "(i.e., the default is for is_index to be false).",
    )


class RelatedChildResource(BaseResource):
    """Keep only type and id of a ChildResource"""

    type: str = Field("child", const=True)


class IndexRelationship(BaseModel):
    """Index Meta-Database relationship"""

    data: Union[None, RelatedChildResource] = Field(
        ...,
        description="JSON API resource linkage. It MUST be either null or contain "
        "a single child identifier object with the fields 'id' and 'type'",
    )


class IndexInfoResource(BaseInfoResource):
    """Index Meta-Database Base URL Info enpoint resource"""

    attributes: IndexInfoAttributes = Field(...)
    relationships: Dict[str, IndexRelationship] = Field(
        ...,
        description="Reference to the child identifier object under the links endpoint "
        "that the provider has chosen as their 'default' OPTIMADE API database. "
        "A client SHOULD present this database as the first choice when an end-user "
        "chooses this provider.",
    )
