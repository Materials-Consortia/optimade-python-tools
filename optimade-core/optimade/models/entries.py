# pylint: disable=line-too-long,no-self-argument
from datetime import datetime
from typing import Optional, Dict, List
from pydantic import BaseModel, Field, validator  # pylint: disable=no-name-in-module

from .jsonapi import Relationships, Attributes, Resource
from .optimade_json import Relationship


__all__ = (
    "EntryRelationships",
    "EntryResourceAttributes",
    "EntryResource",
    "EntryInfoProperty",
    "EntryInfoResource",
)


class TypedRelationship(Relationship):
    # This may be updated when moving to Python 3.8
    @validator("data")
    def check_rel_type(cls, data):
        if hasattr(cls, "_req_type") and any(obj.type != cls._req_type for obj in data):
            raise ValueError("Object stored in relationship data has wrong type")
        return data


class ReferenceRelationship(TypedRelationship):
    _req_type = "references"


class StructureRelationship(TypedRelationship):
    _req_type = "structures"


class EntryRelationships(Relationships):
    """This model wraps the JSON API Relationships to include type-specific top level keys. """

    references: Optional[ReferenceRelationship] = Field(
        None,
        description="Object containing links to relationships with entries of the `references` type.",
    )

    structures: Optional[StructureRelationship] = Field(
        None,
        description="Object containing links to relationships with entries of the `structures` type.",
    )


class EntryResourceAttributes(Attributes):
    """Contains key-value pairs representing the entry's properties."""

    immutable_id: Optional[str] = Field(
        None,
        description="""The entry's immutable ID (e.g., an UUID).
This is important for databases having preferred IDs that point to "the latest version" of a record, but still offer access to older variants.
This ID maps to the version-specific record, in case it changes in the future.
- **Type**: string.
- **Requirements/Conventions**:

  - **Support**: OPTIONAL, i.e., MAY be :val:`null`.
  - **Query**: MUST be a queryable property with support for all mandatory filter features.

- **Examples**:

  - :val:`"8bd3e750-b477-41a0-9b11-3a799f21b44f"`
  - :val:`"fjeiwoj,54;@=%<>#32"` (Strings that are not URL-safe are allowed.)""",
    )

    last_modified: datetime = Field(
        ...,
        description="""Date and time representing when the entry was last modified.
- **Type**: timestamp.
- **Requirements/Conventions**:

  - **Support**: SHOULD be supported, i.e., SHOULD NOT be :val:`null`. Is REQUIRED in this implementation, i.e., MUST NOT be :val:`null`.
  - **Query**: MUST be a queryable property with support for all mandatory filter features.
  - **Response**: REQUIRED in the response unless the query parameter :query-param:`response_fields` is present and does not include this property.

- **Example**:

  - As part of JSON response format: :VAL:`"2007-04-05T14:30Z"` (i.e., encoded as an `RFC 3339 Internet Date/Time Format <https://tools.ietf.org/html/rfc3339#section-5.6>`__ string.)""",
    )


class EntryResource(Resource):

    id: str = Field(
        ...,
        description="""An entry's ID as defined in section `Definition of Terms`_.
- **Type**: string.
- **Requirements/Conventions**:

  - **Support**: REQUIRED, MUST NOT be :val:`null`.
  - **Query**: MUST be a queryable property with support for all mandatory filter features.
  - **Response**: REQUIRED in the response.
  - See section `Definition of Terms`_.

- **Examples**:

  - :val:`"db/1234567"`
  - :val:`"cod/2000000"`
  - :val:`"cod/2000000@1234567"`
  - :val:`"nomad/L1234567890"`
  - :val:`"42"`""",
    )

    type: str = Field(
        ...,
        description="""The name of the type of an entry.
- **Type**: string.
- **Requirements/Conventions**:

  - **Support**: REQUIRED, MUST NOT be :val:`null`.
  - **Query**: MUST be a queryable property with support for all mandatory filter features.
  - **Response**: REQUIRED in the response.
  - MUST be an existing entry type.
  - The entry of type `<type>` and ID `<id>` MUST be returned in response to a request for :endpoint:`/<type>/<id>` under the versioned base URL.

- **Example**: :val:`"structures"`""",
    )

    attributes: EntryResourceAttributes = Field(
        ...,
        description="""a dictionary, containing key-value pairs representing the entry's properties, except for type and id.

Database-provider-specific properties need to include the database-provider-specific prefix
(see appendix `Database-Provider-Specific Namespace Prefixes`_).""",
    )

    relationships: Optional[EntryRelationships] = Field(
        None,
        description="""a dictionary containing references to other entries according to the description in section `Relationships`_
encoded as `JSON API Relationships <https://jsonapi.org/format/1.0/#document-resource-object-relationships>`__.
The OPTIONAL human-readable description of the relationship MAY be provided in the :field:`description` field inside the :field:`meta` dictionary.""",
    )


class EntryInfoProperty(BaseModel):

    description: str = Field(..., description="description of the entry property")

    unit: Optional[str] = Field(
        None, description="the physical unit of the entry property"
    )

    sortable: Optional[bool] = Field(
        None,
        description='defines whether the entry property can be used for sorting with the "sort" parameter. '
        "If the entry listing endpoint supports sorting, this key MUST be present for sortable properties with value `true`.",
    )


class EntryInfoResource(BaseModel):

    formats: List[str] = Field(..., description="list of available output formats.")

    description: str = Field(..., description="description of the entry")

    properties: Dict[str, EntryInfoProperty] = Field(
        ...,
        description="a dictionary describing queryable properties for this "
        "entry type, where each key is a property ID.",
    )

    output_fields_by_format: Dict[str, List[str]] = Field(
        ...,
        description="a dictionary of available output fields for this entry "
        "type, where the keys are the values of the `formats` list "
        "and the values are the keys of the `properties` dictionary.",
    )
