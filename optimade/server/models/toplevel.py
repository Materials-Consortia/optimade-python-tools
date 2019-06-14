from datetime import datetime
from typing import Union, List, Optional

from pydantic import BaseModel, validator, UrlStr, Schema

from optimade.server.models.jsonapi import Link, Links, Resource
from optimade.server.models.structures import StructureResource
from .baseinfo import BaseInfoResource
from optimade.server.models.util import NonnegativeInt
from .errors import ErrorMsg
from .jsonapi import Success, Failure


class OptimadeResponseMetaQuery(BaseModel):
    """ Information on the query that was requested. """
    representation: str = Schema(
        ...,
        description="a string with the part of the URL "
                    "that follows the base URL."
    )

    @validator('representation')
    def representation_must_be_valid_url_with_base(cls, v):
        UrlStr(f'https://baseurl.net{v}')
        return v


class OptimadeProvider(BaseModel):
    """ Stores information on the database provider of the
    implementation.

    """

    name: str = Schema(
        ...,
        description="a short name for the database provider"
    )

    description: str = Schema(
        ...,
        description="a longer description of the database provider"
    )

    prefix: str = Schema(
        ...,
        description="database-provider-specific prefix as found in "
                    "Appendix 1."
    )

    homepage: Optional[Union[UrlStr, Link]] = Schema(
        ...,
        description="a [JSON API links object](http://jsonapi.org/format/1.0#document-links) "
                    "pointing to homepage of the database provider, either "
                    "directly as a string, or as a link object."
    )

    index_base_url: Optional[Union[UrlStr, Link]] = Schema(
        ...,
        description="a [JSON API links object](http://jsonapi.org/format/1.0#document-links) "
                    "pointing to the base URL for the `index` meta-database as "
                    "specified in Appendix 1, either directly as a string, or "
                    "as a link object."
    )


class OptimadeResponseMeta(BaseModel):
    """
    A [JSON API meta member](https://jsonapi.org/format/1.0#document-meta)
    that contains JSON API meta objects of non-standard
    meta-information.

    OPTIONAL additional information global to the query that is not
    specified in this document, MUST start with a
    database-provider-specific prefix.

    """

    query: OptimadeResponseMetaQuery = Schema(
        ...,
        description="information on the query that was requested"
    )

    api_version: str = Schema(
        ...,
        description="a string containing the version of the API "
                    "implementation, e.g. v0.9.5"
    )

    time_stamp: datetime = Schema(
        ...,
        description="a string containing the date and time at which "
                    "the query was exexcuted, in "
                    "[ISO 8601](https://www.iso.org/standard/40874.html) "
                    "format. Times MUST be time-zone aware (i.e. MUST "
                    "NOT be local times), in one of the formats allowed "
                    "by ISO 8601 (i.e. either be in UTC, and then end "
                    "with a Z, or indicate explicitly the offset)."
    )

    data_returned: NonnegativeInt = Schema(
        ...,
        description="an integer containing the number of data objects "
                    "returned for the query."
    )

    more_data_available: bool = Schema(
        ...,
        description="`false` if all data has been returned, and `true` "
                    "if not."
    )

    provider: OptimadeProvider = Schema(
        ...,
        description="information on the database provider of the implementation."
    )

    data_available: Optional[int] = Schema(
        ...,
        description="an integer containing the total number of data "
                    "objects available in the database"
    )

    last_id: Optional[str] = Schema(
        ...,
        description="a string containing the last ID returned"
    )

    response_message: Optional[str] = Schema(
        ...,
        description="response string from the server"
    )

class OptimadeStructureResponse1(Success):
    meta: OptimadeResponseMeta = Schema(..., description="Optimade meta request reply, required")
    data: StructureResource


class OptimadeStructureResponseMany(Success):
    meta: OptimadeResponseMeta
    data: List[StructureResource]


class OptimadeErrorResponse(Failure):
    meta: Optional[OptimadeResponseMeta]
    errors: List[ErrorMsg]


class OptimadeInfoResponse(Success):
    meta: Optional[OptimadeResponseMeta]
    data: BaseInfoResource
