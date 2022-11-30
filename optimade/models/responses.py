# pylint: disable=no-self-argument
from typing import Any, Dict, List, Optional, Union

from pydantic import Field, root_validator

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

    meta: ResponseMeta = StrictField(
        ..., description="A meta object containing non-standard information."
    )
    errors: List[OptimadeError] = StrictField(
        ...,
        description="A list of OPTIMADE-specific JSON API error objects, where the field detail MUST be present.",
        uniqueItems=True,
    )

    @root_validator(pre=True)
    def data_must_be_skipped(cls, values):
        if "data" in values:
            raise ValueError("data MUST be skipped for failures reporting errors.")
        return values


class IndexInfoResponse(Success):
    data: IndexInfoResource = StrictField(
        ..., description="Index meta-database /info data."
    )


class EntryInfoResponse(Success):
    data: EntryInfoResource = StrictField(
        ..., description="OPTIMADE information for an entry endpoint."
    )


class InfoResponse(Success):
    data: BaseInfoResource = StrictField(
        ..., description="The implementations /info data."
    )


class EntryResponseOne(Success):
    data: Union[EntryResource, Dict[str, Any], None] = Field(...)  # type: ignore[assignment]
    included: Optional[Union[List[EntryResource], List[Dict[str, Any]]]] = Field(  # type: ignore[assignment]
        None, uniqueItems=True
    )


class EntryResponseMany(Success):
    data: Union[List[EntryResource], List[Dict[str, Any]]] = Field(  # type: ignore[assignment]
        ..., uniqueItems=True
    )
    included: Optional[Union[List[EntryResource], List[Dict[str, Any]]]] = Field(  # type: ignore[assignment]
        None, uniqueItems=True
    )


class LinksResponse(EntryResponseMany):
    data: Union[List[LinksResource], List[Dict[str, Any]]] = StrictField(
        ...,
        description="List of unique OPTIMADE links resource objects.",
        uniqueItems=True,
    )


class StructureResponseOne(EntryResponseOne):
    data: Union[StructureResource, Dict[str, Any], None] = StrictField(
        ..., description="A single structures entry resource."
    )


class StructureResponseMany(EntryResponseMany):
    data: Union[List[StructureResource], List[Dict[str, Any]]] = StrictField(
        ...,
        description="List of unique OPTIMADE structures entry resource objects.",
        uniqueItems=True,
    )


class ReferenceResponseOne(EntryResponseOne):
    data: Union[ReferenceResource, Dict[str, Any], None] = StrictField(
        ..., description="A single references entry resource."
    )


class ReferenceResponseMany(EntryResponseMany):
    data: Union[List[ReferenceResource], List[Dict[str, Any]]] = StrictField(
        ...,
        description="List of unique OPTIMADE references entry resource objects.",
        uniqueItems=True,
    )
