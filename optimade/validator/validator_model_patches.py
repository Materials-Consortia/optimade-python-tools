""" This class contains patched versions of the OPTiMaDe models as
a workaround for the response field workaround of allowing responses
to contain bare dictionaries. These allow the validator to print detailed
validation responses.

"""

from typing import List

from pydantic import Schema

from optimade.models.optimade_json import Success
from optimade.models import (
    ResponseMeta,
    EntryResource,
    StructureResource,
    ReferenceResource,
)


class ValidatorEntryResponseOne(Success):
    meta: ResponseMeta = Schema(...)
    data: EntryResource = Schema(...)


class ValidatorEntryResponseMany(Success):
    meta: ResponseMeta = Schema(...)
    data: List[EntryResource] = Schema(...)


class ValidatorStructureResponseOne(Success):
    meta: ResponseMeta = Schema(...)
    data: StructureResource = Schema(...)


class ValidatorStructureResponseMany(Success):
    meta: ResponseMeta = Schema(...)
    data: List[StructureResource] = Schema(...)


class ValidatorReferenceResponseOne(Success):
    meta: ResponseMeta = Schema(...)
    data: ReferenceResource = Schema(...)


class ValidatorReferenceResponseMany(Success):
    meta: ResponseMeta = Schema(...)
    data: List[ReferenceResource] = Schema(...)
