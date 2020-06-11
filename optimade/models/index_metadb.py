# pylint: disable=no-self-argument
from pydantic import Field, BaseModel, validator  # pylint: disable=no-name-in-module
from typing import Union, Dict

from .jsonapi import BaseResource
from .baseinfo import BaseInfoAttributes, BaseInfoResource


__all__ = (
    "IndexInfoAttributes",
    "RelatedLinksResource",
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


class RelatedLinksResource(BaseResource):
    """A related Links resource object"""

    type: str = Field("links", const=True)


class IndexRelationship(BaseModel):
    """Index Meta-Database relationship"""

    data: Union[None, RelatedLinksResource] = Field(
        ...,
        description="JSON API resource linkage. It MUST be either null or contain "
        "a single Links identifier object with the fields 'id' and 'type'",
    )


class IndexInfoResource(BaseInfoResource):
    """Index Meta-Database Base URL Info endpoint resource"""

    attributes: IndexInfoAttributes = Field(...)
    relationships: Union[None, Dict[str, IndexRelationship]] = Field(
        ...,
        description="Reference to the child identifier object under the links endpoint "
        "that the provider has chosen as their 'default' OPTIMADE API database. "
        "A client SHOULD present this database as the first choice when an end-user "
        "chooses this provider.",
    )

    @validator("relationships")
    def relationships_key_must_be_default(cls, value):
        if value is not None and all([key != "default" for key in value]):
            raise ValueError(
                "if the relationships value is a dict, the key MUST be 'default'"
            )
        return value
