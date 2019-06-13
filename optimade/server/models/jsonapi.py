"""
This module should reproduce https://jsonapi.org/schema
"""
from typing import Optional

from pydantic import BaseModel, UrlStr, Union


class Link(BaseModel):
    href: UrlStr
    meta: Optional[dict]


class Links(BaseModel):
    next: Optional[Union[UrlStr,Link]]
    base_url: Optional[Union[UrlStr,Link]]


class Resource(BaseModel):
    id: str
    type: str
