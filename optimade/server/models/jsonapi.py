"""
This module should reproduce https://jsonapi.org/schema
"""
from typing import Optional

from pydantic import BaseModel, UrlStr


class Link(BaseModel):
    href: UrlStr
    meta: Optional[dict]


class Links(BaseModel):
    next: Optional[Link]


class Resource(BaseModel):
    id: str
    type: str
