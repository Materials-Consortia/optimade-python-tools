""" This class contains patched versions of the OPTIMADE models as
a workaround for the response field workaround of allowing responses
to contain bare dictionaries. These allow the validator to print detailed
validation responses.

"""

from typing import List, Optional, Dict, Any

from pydantic import Field

from optimade.models.optimade_json import Success
from optimade.models import (
    ResponseMeta,
    EntryResource,
    LinksResource,
    ReferenceResource,
    StructureResource,
)


class ValidatorLinksResponse(Success):
    meta: ResponseMeta = Field(...)
    data: List[LinksResource] = Field(...)


class ValidatorEntryResponseOne(Success):
    meta: ResponseMeta = Field(...)
    data: EntryResource = Field(...)
    included: Optional[List[Dict[str, Any]]] = Field(None)


class ValidatorEntryResponseMany(Success):
    meta: ResponseMeta = Field(...)
    data: List[EntryResource] = Field(...)
    included: Optional[List[Dict[str, Any]]] = Field(None)


class ValidatorReferenceResponseOne(ValidatorEntryResponseOne):
    data: ReferenceResource = Field(...)


class ValidatorReferenceResponseMany(ValidatorEntryResponseMany):
    data: List[ReferenceResource] = Field(...)


class ValidatorStructureResponseOne(ValidatorEntryResponseOne):
    data: StructureResource = Field(...)


class ValidatorStructureResponseMany(ValidatorEntryResponseMany):
    data: List[StructureResource] = Field(...)
