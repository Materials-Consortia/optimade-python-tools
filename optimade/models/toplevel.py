from datetime import datetime
from typing import Union, List, Optional, Dict, Any

from pydantic import BaseModel, AnyHttpUrl, Field, EmailStr

from .jsonapi import Link, Meta
from .utils import NonnegativeInt
from .baseinfo import BaseInfoResource
from .entries import EntryInfoResource, EntryResource
from .index_metadb import IndexInfoResource
from .links import LinksResource
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


class ResponseMetaQuery(BaseModel):
    """ Information on the query that was requested. """

    representation: str = Field(
        ...,
        description="a string with the part of the URL that follows the base URL. Example: '/structures?'",
    )


class Provider(BaseModel):
    """Information on the database provider of the implementation."""

    name: str = Field(..., description="a short name for the database provider")

    description: str = Field(
        ..., description="a longer description of the database provider"
    )

    prefix: str = Field(
        ..., description="database-provider-specific prefix as found in " "Appendix 1."
    )

    homepage: Optional[Union[AnyHttpUrl, Link]] = Field(
        None,
        description="a [JSON API links object](http://jsonapi.org/format/1.0#document-links) "
        "pointing to homepage of the database provider, either "
        "directly as a string, or as a link object.",
    )

    index_base_url: Optional[Union[AnyHttpUrl, Link]] = Field(
        None,
        description="a [JSON API links object](http://jsonapi.org/format/1.0#document-links) "
        "pointing to the base URL for the `index` meta-database as "
        "specified in Appendix 1, either directly as a string, or "
        "as a link object.",
    )


class ImplementationMaintainer(BaseModel):
    """Details about the maintainer of the implementation"""

    email: EmailStr = Field(..., description="the maintainer's email address")


class Implementation(BaseModel):
    """Information on the server implementation"""

    name: Optional[str] = Field(None, description="name of the implementation")

    version: Optional[str] = Field(
        None, description="version string of the current implementation"
    )

    source_url: Optional[AnyHttpUrl] = Field(
        None,
        description="URL of the implementation source, either downloadable archive or version control system",
    )

    maintainer: Optional[ImplementationMaintainer] = Field(
        None,
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

    query: ResponseMetaQuery = Field(
        ..., description="information on the query that was requested"
    )

    api_version: str = Field(
        ...,
        description="a string containing the version of the API "
        "implementation, e.g. v0.9.5",
    )

    time_stamp: datetime = Field(
        ...,
        description="a string containing the date and time at which the query was exexcuted",
    )

    data_returned: NonnegativeInt = Field(
        ...,
        description="an integer containing the number of data objects "
        "returned for the query.",
    )

    more_data_available: bool = Field(
        ..., description="`false` if all data has been returned, and `true` " "if not."
    )

    provider: Provider = Field(
        ..., description="information on the database provider of the implementation."
    )

    data_available: Optional[int] = Field(
        None,
        description="an integer containing the total number of data "
        "objects available in the database",
    )

    last_id: Optional[str] = Field(
        None, description="a string containing the last ID returned"
    )

    response_message: Optional[str] = Field(
        None, description="response string from the server"
    )

    implementation: Optional[Implementation] = Field(
        None, description="a dictionary describing the server implementation"
    )

    warnings: Optional[List[Warnings]] = Field(
        None,
        description="List of warning resource objects representing non-critical errors or warnings. "
        "A warning resource object is defined similarly to a JSON API error object, but MUST also include the field type, "
        'which MUST have the value "warning". The field detail MUST be present and SHOULD contain a non-critical message, '
        "e.g., reporting unrecognized search attributes or deprecated features. The field status, representing a HTTP "
        "response status code, MUST NOT be present for a warning resource object. This is an exclusive field for error resource objects.",
    )


class ErrorResponse(Failure):
    meta: Optional[ResponseMeta] = Field(None)
    errors: List[Error] = Field(...)


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
