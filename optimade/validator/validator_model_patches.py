""" This class contains patched versions of the OPTiMaDe models as
a workaround for the response field workaround of allowing responses
to contain bare dictionaries. These allow the validator to print detailed
validation responses.

"""

from typing import List, Optional, Dict, Any

from pydantic import Schema

from optimade.models.optimade_json import Success
from optimade.models import (
    ResponseMeta,
    EntryResource,
    LinksResource,
    ReferenceResource,
    StructureResource,
)


class ValidatorLinksResponse(Success):
    meta: ResponseMeta = Schema(...)
    data: List[LinksResource] = Schema(...)


class ValidatorEntryResponseOne(Success):
    meta: ResponseMeta = Schema(...)
    data: EntryResource = Schema(...)
    included: Optional[List[Dict[str, Any]]] = Schema(...)


class ValidatorEntryResponseMany(Success):
    meta: ResponseMeta = Schema(...)
    data: List[EntryResource] = Schema(...)
    included: Optional[List[Dict[str, Any]]] = Schema(...)


class ValidatorReferenceResponseOne(ValidatorEntryResponseOne):
    data: ReferenceResource = Schema(...)


class ValidatorReferenceResponseMany(ValidatorEntryResponseMany):
    data: List[ReferenceResource] = Schema(...)


class ValidatorStructureResponseOne(ValidatorEntryResponseOne):
    data: StructureResource = Schema(...)


class ValidatorStructureResponseMany(ValidatorEntryResponseMany):
    data: List[StructureResource] = Schema(...)
