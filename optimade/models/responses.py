# pylint: disable=no-self-argument
from typing import Union, List, Optional, Dict, Any

from pydantic import Field, root_validator

from .jsonapi import Response
from .baseinfo import BaseInfoResource
from .entries import EntryInfoResource, EntryResource
from .index_metadb import IndexInfoResource
from .links import LinksResource
from .optimade_json import Success, ResponseMeta, OptimadeError
from .references import ReferenceResource
from .structures import StructureResource


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

    meta: Optional[ResponseMeta] = Field(
        None, description="A meta object containing non-standard information"
    )
    errors: List[OptimadeError] = Field(
        ...,
        description="A list of OPTiMaDe-specific JSON API error objects, where the field detail MUST be present.",
        uniqueItems=True,
    )

    @root_validator(pre=True)
    def data_must_be_skipped(cls, values):
        if values.get("data", None) is not None:
            raise ValueError("data MUST be skipped for failures reporting errors")
        return values


class IndexInfoResponse(Success):
    data: IndexInfoResource = Field(...)


class EntryInfoResponse(Success):
    data: EntryInfoResource = Field(...)


class InfoResponse(Success):
    data: BaseInfoResource = Field(...)


class EntryResponseOne(Success):
    data: Union[EntryResource, Dict[str, Any], None] = Field(...)
    included: Optional[Union[List[EntryResource], List[Dict[str, Any]]]] = Field(
        None, uniqueItems=True
    )


class EntryResponseMany(Success):
    data: Union[List[EntryResource], List[Dict[str, Any]]] = Field(
        ..., uniqueItems=True
    )
    included: Optional[Union[List[EntryResource], List[Dict[str, Any]]]] = Field(
        None, uniqueItems=True
    )


class LinksResponse(EntryResponseMany):
    data: Union[List[LinksResource], List[Dict[str, Any]]] = Field(
        ..., uniqueItems=True
    )


class StructureResponseOne(EntryResponseOne):
    data: Union[StructureResource, Dict[str, Any], None] = Field(...)


class StructureResponseMany(EntryResponseMany):
    data: Union[List[StructureResource], List[Dict[str, Any]]] = Field(
        ..., uniqueItems=True
    )


class ReferenceResponseOne(EntryResponseOne):
    data: Union[ReferenceResource, Dict[str, Any], None] = Field(...)


class ReferenceResponseMany(EntryResponseMany):
    data: Union[List[ReferenceResource], List[Dict[str, Any]]] = Field(
        ..., uniqueItems=True
    )
