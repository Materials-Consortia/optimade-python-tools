from typing import Annotated, Any, Optional, Union

from pydantic import model_validator

from optimade.models.baseinfo import BaseInfoResource
from optimade.models.entries import EntryInfoResource, EntryResource
from optimade.models.index_metadb import IndexInfoResource
from optimade.models.jsonapi import Response
from optimade.models.links import LinksResource
from optimade.models.optimade_json import OptimadeError, ResponseMeta, Success
from optimade.models.references import ReferenceResource
from optimade.models.structures import StructureResource
from optimade.models.utils import StrictField

__all__ = (
    "ErrorResponse",
    "EntryInfoResponse",
    "IndexInfoResponse",
    "InfoResponse",
    "LinksResponse",
    "EntryResponseOne",
    "EntryResponseMany",
    "StructureResponseOne",
    "StructureResponseMany",
    "ReferenceResponseOne",
    "ReferenceResponseMany",
)


class ErrorResponse(Response):
    """errors MUST be present and data MUST be skipped"""

    meta: Annotated[
        ResponseMeta,
        StrictField(description="A meta object containing non-standard information."),
    ]
    errors: Annotated[
        list[OptimadeError],
        StrictField(
            description="A list of OPTIMADE-specific JSON API error objects, where the field detail MUST be present.",
            uniqueItems=True,
        ),
    ]

    @model_validator(mode="after")
    def data_must_be_skipped(self) -> "ErrorResponse":
        if self.data or "data" in self.model_fields_set:
            raise ValueError("data MUST be skipped for failures reporting errors.")
        return self


class IndexInfoResponse(Success):
    data: Annotated[
        IndexInfoResource, StrictField(description="Index meta-database /info data.")
    ]


class EntryInfoResponse(Success):
    data: Annotated[
        EntryInfoResource,
        StrictField(description="OPTIMADE information for an entry endpoint."),
    ]


class InfoResponse(Success):
    data: Annotated[
        BaseInfoResource, StrictField(description="The implementations /info data.")
    ]


class EntryResponseOne(Success):
    data: Annotated[
        Optional[Union[EntryResource, dict[str, Any]]],
        StrictField(
            description="The single entry resource returned by this query.",
            union_mode="left_to_right",
        ),
    ] = None  # type: ignore[assignment]
    included: Annotated[
        Optional[Union[list[EntryResource], list[dict[str, Any]]]],
        StrictField(
            description="A list of unique included OPTIMADE entry resources.",
            uniqueItems=True,
            union_mode="left_to_right",
        ),
    ] = None  # type: ignore[assignment]


class EntryResponseMany(Success):
    data: Annotated[  # type: ignore[assignment]
        Union[list[EntryResource], list[dict[str, Any]]],
        StrictField(
            description="List of unique OPTIMADE entry resource objects.",
            uniqueItems=True,
            union_mode="left_to_right",
        ),
    ]
    included: Annotated[
        Optional[Union[list[EntryResource], list[dict[str, Any]]]],
        StrictField(
            description="A list of unique included OPTIMADE entry resources.",
            uniqueItems=True,
            union_mode="left_to_right",
        ),
    ] = None  # type: ignore[assignment]


class LinksResponse(EntryResponseMany):
    data: Annotated[
        Union[list[LinksResource], list[dict[str, Any]]],
        StrictField(
            description="List of unique OPTIMADE links resource objects.",
            uniqueItems=True,
            union_mode="left_to_right",
        ),
    ]


class StructureResponseOne(EntryResponseOne):
    data: Annotated[
        Optional[Union[StructureResource, dict[str, Any]]],
        StrictField(
            description="A single structures entry resource.",
            union_mode="left_to_right",
        ),
    ]


class StructureResponseMany(EntryResponseMany):
    data: Annotated[
        Union[list[StructureResource], list[dict[str, Any]]],
        StrictField(
            description="List of unique OPTIMADE structures entry resource objects.",
            uniqueItems=True,
            union_mode="left_to_right",
        ),
    ]


class ReferenceResponseOne(EntryResponseOne):
    data: Annotated[
        Optional[Union[ReferenceResource, dict[str, Any]]],
        StrictField(
            description="A single references entry resource.",
            union_mode="left_to_right",
        ),
    ]


class ReferenceResponseMany(EntryResponseMany):
    data: Annotated[
        Union[list[ReferenceResource], list[dict[str, Any]]],
        StrictField(
            description="List of unique OPTIMADE references entry resource objects.",
            uniqueItems=True,
            union_mode="left_to_right",
        ),
    ]
