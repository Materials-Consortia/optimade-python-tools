from typing import Dict, List, Optional

from pydantic import BaseModel, UrlStr, Schema
from .modified_jsonapi import Resource


class BaseInfoAttributes(BaseModel):
    api_version: str = Schema(...)
    available_api_versions: Dict[str, UrlStr]
    formats: List[str] = ["jsonapi"]
    entry_types_by_format: Dict[str, List[str]]
    available_endpoints: List[str] = Schema(...)
    is_index: Optional[bool] = Schema(default=False, const=True)


class BaseInfoResource(Resource):
    id: str = Schema(default="/", const=True)
    type: str = Schema(default="info", const=True)
    attributes: BaseInfoAttributes = Schema(...)
