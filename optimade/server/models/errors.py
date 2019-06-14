from typing import Dict, List, Optional, Union

from .jsonapi import Link
from .modified_jsonapi import Links
from pydantic import BaseModel, UrlStr, Schema

class ErrorSource(BaseModel):
     pointer: Optional[str]=Schema(..., description='a JSON Pointer [RFC6901] to the associated entity in the request document [e.g. "/data" for a primary data object, or "/data/attributes/title" for a specific attribute].')
     parameter: Optional[str]=Schema(..., description='a string indicating which URI query parameter caused the error.')


class ErrorMsg(BaseModel):
    id: str=Schema(..., description="a unique identifier for this particular occurrence of the problem.")
    links: Dict[str, Union[str, Link]]=Schema(..., description="a list of links objects.")
    status: str=Schema(..., description="the HTTP status code applicable to this problem, expressed as a string value.")
    code: str=Schema(..., description="an application-specific error code, expressed as a string value.")
    title: str=Schema(..., description="a short, human-readable summary of the problem that SHOULD NOT change from occurrence to occurrence of the problem, except for purposes of localization.")
    detail: str=Schema(..., description="a human-readable explanation specific to this occurrence of the problem. Like title, this field’s value can be localized.")
    source: ErrorSource=Schema(..., description="an object containing references to the source of the error")
    meta: dict=Schema(..., description="a meta object containing non-standard meta-information about the error.")
