"""
Modified jsonapi for OptimadeAPI
"""
from optimade.server.models import jsonapi
from datetime import datetime
from pydantic import  UrlStr, BaseModel
from typing import Optional, Union, Any

class Attributes(jsonapi.Attributes):
    """Modification of Attributes to include Optimade specified keys"""
    local_id: UrlStr
    lad_modified: datetime
    immutable_id: Optional[UrlStr]

class ErrorLinks(BaseModel):
    """Links with recast for Errors"""
    about: Union[jsonapi.Link, UrlStr]

class Error(jsonapi.Error):
    """Error where links uses ErrorLinks"""
    links: Optional[ErrorLinks]

class Links(jsonapi.Links):
    """Links now store base_url"""
    base_rul: Optional[Union[jsonapi.Link, UrlStr]]
