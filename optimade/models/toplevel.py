from datetime import datetime
from typing import Union, List, Optional, Dict, Any

from pydantic import BaseModel, validator, UrlStr, Schema, EmailStr

from .jsonapi import Link, Meta
from .util import NonnegativeInt
from .baseinfo import BaseInfoResource
from .entries import EntryInfoResource, EntryResource
from .optimade_json import Error, Success, Failure, Warnings
from .references import ReferenceResource
from .structures import StructureResource


__all__ = (
    "ResponseMetaQuery",
    "Provider",
    "ImplementationMaintainer",
    "Implementation",
    "ResponseMeta",
    "ErrorResponse",
    "EntryInfoResponse",
    "InfoResponse",
    "EntryResponseOne",
    "EntryResponseMany",
    "StructureResponseOne",
    "StructureResponseMany",
    "ReferenceResponseOne",
    "ReferenceResponseMany",
)


class ResponseMetaQuery(BaseModel):
    """ Information on the query that was requested. """

    representation: str = Schema(
        ...,
        description="a string with the part of the URL " "that follows the base URL.",
    )

    @validator("representation")
    def representation_must_be_valid_url_with_base(cls, v):
        UrlStr(f"https://baseurl.net{v}")
        return v


class Provider(BaseModel):
    """Information on the database provider of the implementation."""

    name: str = Schema(..., description="a short name for the database provider")

    description: str = Schema(
        ..., description="a longer description of the database provider"
    )

    prefix: str = Schema(
        ..., description="database-provider-specific prefix as found in " "Appendix 1."
    )

    homepage: Optional[Union[UrlStr, Link]] = Schema(
        ...,
        description="a [JSON API links object](http://jsonapi.org/format/1.0#document-links) "
        "pointing to homepage of the database provider, either "
        "directly as a string, or as a link object.",
    )

    index_base_url: Optional[Union[UrlStr, Link]] = Schema(
        ...,
        description="a [JSON API links object](http://jsonapi.org/format/1.0#document-links) "
        "pointing to the base URL for the `index` meta-database as "
        "specified in Appendix 1, either directly as a string, or "
        "as a link object.",
    )


class ImplementationMaintainer(BaseModel):
    """Details about the maintainer of the implementation"""

    email: EmailStr = Schema(..., description="the maintainer's email address")


class Implementation(BaseModel):
    """Information on the server implementation"""

    name: Optional[str] = Schema(..., description="name of the implementation")

    version: Optional[str] = Schema(
        ..., description="version string of the current implementation"
    )

    source_url: Optional[UrlStr] = Schema(
        ...,
        description="URL of the implementation source, either downloadable archive or version control system",
    )

    maintainer: Optional[ImplementationMaintainer] = Schema(
        ...,
        description="A dictionary providing details about the maintainer of the implementation.",
    )


class ResponseMeta(Meta):
    """
    A [JSON API meta member](https://jsonapi.org/format/1.0#document-meta)
    that contains JSON API meta objects of non-standard
    meta-information.

    OPTIONAL additional information global to the query that is not
    specified in this document, MUST start with a
    database-provider-specific prefix.
    """

    query: ResponseMetaQuery = Schema(
        ..., description="information on the query that was requested"
    )

    api_version: str = Schema(
        ...,
        description="a string containing the version of the API "
        "implementation, e.g. v0.9.5",
    )

    time_stamp: datetime = Schema(
        ...,
        description="a string containing the date and time at which the query was exexcuted",
    )

    data_returned: NonnegativeInt = Schema(
        ...,
        description="an integer containing the number of data objects "
        "returned for the query.",
    )

    more_data_available: bool = Schema(
        ..., description="`false` if all data has been returned, and `true` " "if not."
    )

    provider: Provider = Schema(
        ..., description="information on the database provider of the implementation."
    )

    data_available: Optional[int] = Schema(
        ...,
        description="an integer containing the total number of data "
        "objects available in the database",
    )

    last_id: Optional[str] = Schema(
        ..., description="a string containing the last ID returned"
    )

    response_message: Optional[str] = Schema(
        ..., description="response string from the server"
    )

    implementation: Optional[Implementation] = Schema(
        ..., description="a dictionary describing the server implementation"
    )

    warnings: Optional[List[Warnings]] = Schema(
        ...,
        description="List of warning resource objects representing non-critical errors or warnings. "
        "A warning resource object is defined similarly to a JSON API error object, but MUST also include the field type, "
        'which MUST have the value "warning". The field detail MUST be present and SHOULD contain a non-critical message, '
        "e.g., reporting unrecognized search attributes or deprecated features. The field status, representing a HTTP "
        "response status code, MUST NOT be present for a warning resource object. This is an exclusive field for error resource objects.",
    )


class ErrorResponse(Failure):
    meta: Optional[ResponseMeta] = Schema(...)
    errors: List[Error] = Schema(...)


class EntryInfoResponse(Success):
    meta: Optional[ResponseMeta] = Schema(...)
    data: EntryInfoResource = Schema(...)


class InfoResponse(Success):
    meta: Optional[ResponseMeta] = Schema(...)
    data: BaseInfoResource = Schema(...)


class EntryResponseOne(Success):
    meta: ResponseMeta = Schema(...)
    data: Union[EntryResource, Dict[str, Any], None] = Schema(...)
    included: Optional[Union[List[EntryResource], List[Dict[str, Any]]]] = Schema(...)


class EntryResponseMany(Success):
    meta: ResponseMeta = Schema(...)
    data: Union[List[EntryResource], List[Dict[str, Any]]] = Schema(...)
    included: Optional[Union[List[EntryResource], List[Dict[str, Any]]]] = Schema(...)


class StructureResponseOne(EntryResponseOne):
    data: Union[StructureResource, Dict[str, Any], None] = Schema(...)


class StructureResponseMany(EntryResponseMany):
    data: Union[List[StructureResource], List[Dict[str, Any]]] = Schema(...)


class ReferenceResponseOne(EntryResponseOne):
    data: Union[ReferenceResource, Dict[str, Any], None] = Schema(...)


class ReferenceResponseMany(EntryResponseMany):
    data: Union[List[ReferenceResource], List[Dict[str, Any]]] = Schema(...)
