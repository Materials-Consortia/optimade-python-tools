from datetime import datetime
from typing import Optional, Dict, List

from pydantic import BaseModel

from .jsonapi import Resource


class EntryResourceAttributes(BaseModel):
    local_id: str
    last_modified: datetime
    immutable_id: Optional[str]


class EntryResource(Resource):
    attributes: EntryResourceAttributes


class EntryPropertyInfo(BaseModel):
    description: str
    unit: Optional[str]


class EntryInfoAttributes(BaseModel):
    description: str
    properties: Dict[str, EntryPropertyInfo]
    formats: List[str] = ["json"]
    output_fields_by_format: Dict[str, List[str]]


class EntryInfoResource(BaseModel):
    id: str
    type: str = "info"
    attributes: EntryInfoAttributes
