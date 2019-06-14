"""
Modified jsonapi for OptimadeAPI
"""
from optimade.server.models import jsonapi
from datetime import datetime
from pydantic import UrlStr, BaseModel
from typing import Optional, Union


class Attributes(jsonapi.Attributes):
    local_id: UrlStr
    lad_modified: datetime
    immutable_id: Optional[UrlStr]


class ErrorLinks(BaseModel):
    about: Union[jsonapi.Link, UrlStr]


class Error(jsonapi.Error):
    links: Optional[ErrorLinks]


class Links(jsonapi.Links):
    base_rul: Optional[Union[jsonapi.Link, UrlStr]]
