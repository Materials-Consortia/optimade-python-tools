from datetime import datetime
from typing import Union, List

from pydantic import BaseModel, validator, UrlStr, Schema

from optimade.server.models.jsonapi import Links, Resource
from optimade.server.models.structures import StructureResource
from optimade.server.models.util import NonnegativeInt


class OptimadeResponseMetaQuery(BaseModel):
    representation: str

    @validator('representation')
    def representation_must_be_valid_url_with_base(cls, v):
        UrlStr(f'https://baseurl.net{v}')
        return v


class OptimadeResponseMeta(BaseModel):
    """
    A JSON API meta member that contains JSON API meta objects of non-standard meta-information.

    In addition to the required fields, it MAY contain

    - `data_available`: an integer containing the total number of data objects available in the database.
    - `last_id`: a string containing the last ID returned.
    - `response_message`: response string from the server.

    Other OPTIONAL additional information global to the query that is not specified in this document, MUST start with
    a database-provider-specific prefix
    """
    query: OptimadeResponseMetaQuery
    api_version: str = Schema(..., description="a string containing the version of the API implementation.")
    time_stamp: datetime
    data_returned: NonnegativeInt
    more_data_available: bool


class OptimadeResponse1(BaseModel):
    links: Links
    meta: OptimadeResponseMeta
    data: Resource


class OptimadeResponseMany(BaseModel):
    links: Links
    meta: OptimadeResponseMeta
    data: List[Resource]


class OptimadeStructureResponse1(OptimadeResponse1):
    data: StructureResource


class OptimadeStructureResponseMany(OptimadeResponseMany):
    data: List[StructureResource]
