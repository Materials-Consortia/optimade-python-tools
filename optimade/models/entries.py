from datetime import datetime
from typing import Optional, Dict, List
from pydantic import BaseModel, Schema

from .jsonapi import Relationships, Attributes, Resource


__all__ = ("EntryResource", "EntryResourceAttributes", "EntryInfoResource")


class EntryResourceAttributes(Attributes):
    """Contains key-value pairs representing the entry's properties."""

    immutable_id: Optional[str] = Schema(
        ...,
        description="""The entry's immutable ID (e.g., an UUID).
This is important for databases having preferred IDs that point to "the latest version" of a record, but still offer access to older variants.
This ID maps to the version-specific record, in case it changes in the future.
- **Type**: string.
- **Requirements/Conventions**:

  - **Response**: OPTIONAL in the response.
  - **Query**: If present, MUST be a queryable property with support for all mandatory filter operators.

- **Examples**:

  - :val:`"8bd3e750-b477-41a0-9b11-3a799f21b44f"` 
  - :val:`"fjeiwoj,54;@=%<>#32"` (Strings that are not URL-safe are allowed.)""",
    )

    last_modified: datetime = Schema(
        ...,
        description="""Date and time representing when the entry was last modified.
- **Type**: timestamp.
- **Requirements/Conventions**:

  - **Response**: REQUIRED in the response unless explicitly excluded.
  - **Query**: MUST be a queryable property with support for all mandatory filter operators.

- **Example**:

  - As part of JSON response format: :VAL:`"2007-04-05T14:30Z"`
    (i.e., encoded as an `RFC 3339 Internet Date/Time Format <https://tools.ietf.org/html/rfc3339#section-5.6>`__ string.)""",
    )


class EntryResource(Resource):

    id: str = Schema(
        ...,
        description="""An entry's ID as defined in section `Definition of Terms`_.
- **Type**: string.
- **Requirements/Conventions**:

  - **Response**: REQUIRED in the response unless explicitly excluded.
  - **Query**: MUST be a queryable property with support for all mandatory filter operators.
  - See section `Definition of Terms`_.

- **Examples**:

  - :val:`"db/1234567"`
  - :val:`"cod/2000000"`
  - :val:`"cod/2000000@1234567"`
  - :val:`"nomad/L1234567890"`
  - :val:`"42"`""",
    )

    type: str = Schema(
        ...,
        description="""The name of the type of an entry.
Any entry MUST be able to be fetched using the `base URL <Base URL_>`_ type and ID at the url :endpoint:`<base URL>/<type>/<id>`.
- **Type**: string.
- **Requirements/Conventions**:

  - **Response**: REQUIRED in the response unless explicitly excluded.
  - **Query**: Support for queries on this property is OPTIONAL.
    If supported, only a subset of string comparison operators MAY be supported.

- **Requirements/Conventions**: MUST be an existing entry type.
- **Example**: :val:`"structures"`""",
    )

    attributes: EntryResourceAttributes = Schema(
        ...,
        description="""a dictionary, containing key-value pairs representing the entry's properties, except for type and id.

Database-provider-specific properties need to include the database-provider-specific prefix
(see appendix `Database-Provider-Specific Namespace Prefixes`_).""",
    )

    relationships: Optional[Relationships] = Schema(
        ...,
        description="""a dictionary containing references to other entries according to the description in section `Relationships`_
encoded as `JSON API Relationships <https://jsonapi.org/format/1.0/#document-resource-object-relationships>`__.
The OPTIONAL human-readable description of the relationship MAY be provided in the :field:`description` field inside the :field:`meta` dictionary.""",
    )


class EntryInfoProperty(BaseModel):

    description: str = Schema(..., description="description of the entry")

    unit: Optional[str] = Schema(..., description="the physical unit of the entry")


class EntryInfoResource(BaseModel):

    formats: List[str] = Schema(..., description="list of available output formats.")

    description: str = Schema(..., description="description of the entry")

    properties: Dict[str, EntryInfoProperty] = Schema(
        ...,
        description="a dictionary describing queryable properties for this "
        "entry type, where each key is a property ID.",
    )

    output_fields_by_format: Dict[str, List[str]] = Schema(
        ...,
        description="a dictionary of available output fields for this entry "
        "type, where the keys are the values of the `formats` list "
        "and the values are the keys of the `properties` dictionary.",
    )
