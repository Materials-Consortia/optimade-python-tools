from typing import Union, List, Optional, Dict, Any

from pydantic import Field

from .baseinfo import BaseInfoResource
from .entries import EntryInfoResource, EntryResource
from .index_metadb import IndexInfoResource
from .links import LinksResource
from .optimade_json import Success, Failure, ResponseMeta
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


class ErrorResponse(Failure):
    meta: Optional[ResponseMeta] = Field(None)


class IndexInfoResponse(Success):
    meta: Optional[ResponseMeta] = Field(None)
    data: IndexInfoResource = Field(...)


class EntryInfoResponse(Success):
    meta: Optional[ResponseMeta] = Field(None)
    data: EntryInfoResource = Field(...)


class InfoResponse(Success):
    meta: Optional[ResponseMeta] = Field(None)
    data: BaseInfoResource = Field(...)


class EntryResponseOne(Success):
    meta: Optional[ResponseMeta] = Field(None)
    data: Union[EntryResource, Dict[str, Any], None] = Field(...)
    included: Optional[Union[List[EntryResource], List[Dict[str, Any]]]] = Field(None)


class EntryResponseMany(Success):
    meta: Optional[ResponseMeta] = Field(None)
    data: Union[List[EntryResource], List[Dict[str, Any]]] = Field(...)
    included: Optional[Union[List[EntryResource], List[Dict[str, Any]]]] = Field(None)


class LinksResponse(EntryResponseMany):
    data: Union[List[LinksResource], List[Dict[str, Any]]] = Field(...)


class StructureResponseOne(EntryResponseOne):
    data: Union[StructureResource, Dict[str, Any], None] = Field(...)


class StructureResponseMany(EntryResponseMany):
    data: Union[List[StructureResource], List[Dict[str, Any]]] = Field(...)


class ReferenceResponseOne(EntryResponseOne):
    data: Union[ReferenceResource, Dict[str, Any], None] = Field(...)


class ReferenceResponseMany(EntryResponseMany):
    data: Union[List[ReferenceResource], List[Dict[str, Any]]] = Field(...)
