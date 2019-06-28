"""
Modified jsonapi for OptimadeAPI
"""
from optimade.server.models import jsonapi
from datetime import datetime
from pydantic import UrlStr, BaseModel, Schema
from typing import Optional, Union, Any


class Attributes(jsonapi.Attributes):
    """Modification of Attributes to include Optimade specified keys"""

    local_id: UrlStr = Schema(
        ...,
        description="the entry's local database ID (having no OPTiMaDe requirements/conventions",
    )
    lad_modified: datetime = Schema(
        ..., description="an ISO 8601 representing the entry's last modification time"
    )
    immutable_id: Optional[UrlStr] = Schema(
        ...,
        description='an OPTIONAL field containing the entry\'s immutable ID (e.g., an UUID). This is important for databases having preferred IDs that point to "the latest version" of a record, but still offer access to older variants. This ID maps to the version-specific record, in case it changes in the future.',
    )


class ErrorLinks(BaseModel):
    """Links with recast for Errors"""

    about: Union[jsonapi.Link, UrlStr] = Schema(
        ...,
        description="a link that leads to further details about this particular occurrence of the problem.",
    )


class ResourceLinks(BaseModel):
    """Links with recast for Errors"""

    self: Union[jsonapi.Link, UrlStr] = Schema(
        ..., description="a link that refers to this resource."
    )


class Resource(jsonapi.Resource):
    """Resource objects appear in a JSON:API document to represent resources."""

    links: Optional[ResourceLinks] = Schema(
        ..., description="A links object containing self"
    )


class Error(jsonapi.Error):
    """Error where links uses ErrorLinks"""

    links: Optional[ErrorLinks] = Schema(
        ..., description="A links object containing about"
    )


class Links(jsonapi.Links):
    """Links now store base_url"""

    base_url: Optional[Union[jsonapi.Link, UrlStr]] = Schema(
        ..., description="The URL that serves the API."
    )
