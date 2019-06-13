from datetime import datetime
from typing import Optional, Dict, List

from pydantic import BaseModel, Schema

from .jsonapi import Link, Links, Resource, Relationships, Meta


class EntryResourceAttributes(BaseModel):
    """ Contains key-value pairs representing the entry's properties. """

    local_id: str = Schema(
        ...,
        description="the entry's local database ID (having no OPTiMaDe "
                    "requirements/conventions)"
    )

    last_modified: datetime = Schema(
        ...,
        description="an [ISO 8601](https://www.iso.org/standard/40874.html) "
                    "representing the entry's last modification time."
    )

    immutable_id: Optional[str] = Schema(
        ...,
        description="an optional field containing the entry's immutable ID "
                    "(e.g. a UUID). This is important for databases having "
                    "preferred IDs that point to 'the latest version' of a "
                    "record, but still offer access to older variants. This ID "
                    "maps to the version-specific record, in case it changes "
                    "in the future."
    )


class EntryResource(Resource):

    type: str = Schema(
        ...,
        description="field containing the type of the entry"
    )

    id: str = Schema(
        ...,
        description="a string which together with the type uniquely identifies "
                    "the object and strictly follows the requirements as "
                    "specified by `id`. This can be the local database ID."
    )

    attributes: EntryResourceAttributes = Schema(
        ...,
        description="a dictionary containing key-value pairs representing the "
                    "entry's properties."
    )

    links: Optional[Links] = Schema(
        ...,
        description="a JSON API links object"
    )

    meta: Optional[Meta] = Schema(
        ...,
        description="a JSON API meta object that contains non-standard "
                    "information about the object."
    )

    relationships: Optional[Relationships] = Schema(
        ...,
        description="a dictionary containing references to other resource "
                    "objects as defined by the JSON API relationships object."
    )


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
