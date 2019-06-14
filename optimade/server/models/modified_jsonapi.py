from optimade.server.models.jsonapi import Link, Links, Source

from datetime import datetime
from pydantic import  UrlStr, BaseModel
from typing import Optional, Union, Any

class Attributes(BaseModel):
    local_id: UrlStr
    lad_modified: datetime
    immutable_id: Optional[UrlStr]

class ErrorLinks(BaseModel):
    about: Union[Link, UrlStr]

class Error(BaseModel):
    id: Optional[str]
    status: Optional[str]
    code: Optional[str]
    title: Optional[str]
    detail: Optional[str]
    source: Optional[Source]
    meta: Optional[dict]
    links: Optional[ErrorLinks]

class Links(Links):
    base_rul: Optional[Union[Link, UrlStr]]
