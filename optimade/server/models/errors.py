from typing import Dict, List, Optional, Union

from .jsonapi import Error, Link
from pydantic import BaseModel, UrlStr, Schema

class ErrorLinks(BaseModel):
     about: Union[str, Link] = Schema(..., description="a link that leads to further details about this particular occurrence of the problem.")

class ErrorMsg(Error):
     links: ErrorLinks
