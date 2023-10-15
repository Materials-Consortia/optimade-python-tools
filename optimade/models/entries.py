from datetime import datetime
from typing import Annotated, Any, ClassVar, Literal, Optional, Union

from pydantic import BaseModel, field_validator

from optimade.models.jsonapi import Attributes, Relationships, Resource
from optimade.models.optimade_json import (
    BaseRelationshipResource,
    DataType,
    Relationship,
)
from optimade.models.utils import OptimadeField, StrictField, SupportLevel

__all__ = (
    "EntryRelationships",
    "EntryResourceAttributes",
    "EntryResource",
    "EntryInfoProperty",
    "EntryInfoResource",
)


class TypedRelationship(Relationship):
    _req_type: ClassVar[str]

    @field_validator("data", mode="after")
    @classmethod
    def check_rel_type(
        cls, data: Union[BaseRelationshipResource, list[BaseRelationshipResource]]
    ) -> list[BaseRelationshipResource]:
        if not isinstance(data, list):
            # All relationships at this point are empty-to-many relationships in JSON:API:
            # https://jsonapi.org/format/1.0/#document-resource-object-linkage
            raise ValueError("`data` key in a relationship must always store a list.")

        if any(obj.type != cls._req_type for obj in data):
            raise ValueError("Object stored in relationship data has wrong type")

        return data


class ReferenceRelationship(TypedRelationship):
    _req_type: ClassVar[Literal["references"]] = "references"


class StructureRelationship(TypedRelationship):
    _req_type: ClassVar[Literal["structures"]] = "structures"


class EntryRelationships(Relationships):
    """This model wraps the JSON API Relationships to include type-specific top level keys."""

    references: Annotated[
        Optional[ReferenceRelationship],
        StrictField(
            description="Object containing links to relationships with entries of the `references` type.",
        ),
    ] = None

    structures: Annotated[
        Optional[StructureRelationship],
        StrictField(
            description="Object containing links to relationships with entries of the `structures` type.",
        ),
    ] = None


class EntryResourceAttributes(Attributes):
    """Contains key-value pairs representing the entry's properties."""

    immutable_id: Annotated[
        Optional[str],
        OptimadeField(
            description="""The entry's immutable ID (e.g., an UUID). This is important for databases having preferred IDs that point to "the latest version" of a record, but still offer access to older variants. This ID maps to the version-specific record, in case it changes in the future.

- **Type**: string.

- **Requirements/Conventions**:
    - **Support**: OPTIONAL support in implementations, i.e., MAY be `null`.
    - **Query**: MUST be a queryable property with support for all mandatory filter features.

- **Examples**:
    - `"8bd3e750-b477-41a0-9b11-3a799f21b44f"`
    - `"fjeiwoj,54;@=%<>#32"` (Strings that are not URL-safe are allowed.)""",
            support=SupportLevel.OPTIONAL,
            queryable=SupportLevel.MUST,
        ),
    ] = None

    last_modified: Annotated[
        Optional[datetime],
        OptimadeField(
            description="""Date and time representing when the entry was last modified.

- **Type**: timestamp.

- **Requirements/Conventions**:
    - **Support**: SHOULD be supported by all implementations, i.e., SHOULD NOT be `null`.
    - **Query**: MUST be a queryable property with support for all mandatory filter features.
    - **Response**: REQUIRED in the response unless the query parameter `response_fields` is present and does not include this property.

- **Example**:
    - As part of JSON response format: `"2007-04-05T14:30:20Z"` (i.e., encoded as an [RFC 3339 Internet Date/Time Format](https://tools.ietf.org/html/rfc3339#section-5.6) string.)""",
            support=SupportLevel.SHOULD,
            queryable=SupportLevel.MUST,
        ),
    ]

    @field_validator("immutable_id", mode="before")
    @classmethod
    def cast_immutable_id_to_str(cls, value: Any) -> str:
        """Convenience validator for casting `immutable_id` to a string."""
        if value is not None and not isinstance(value, str):
            value = str(value)

        return value


class EntryResource(Resource):
    """The base model for an entry resource."""

    id: Annotated[
        str,
        OptimadeField(
            description="""An entry's ID as defined in section Definition of Terms.

- **Type**: string.

- **Requirements/Conventions**:
    - **Support**: MUST be supported by all implementations, MUST NOT be `null`.
    - **Query**: MUST be a queryable property with support for all mandatory filter features.
    - **Response**: REQUIRED in the response.

- **Examples**:
    - `"db/1234567"`
    - `"cod/2000000"`
    - `"cod/2000000@1234567"`
    - `"nomad/L1234567890"`
    - `"42"`""",
            support=SupportLevel.MUST,
            queryable=SupportLevel.MUST,
        ),
    ]

    type: Annotated[
        str,
        OptimadeField(
            description="""The name of the type of an entry.

- **Type**: string.

- **Requirements/Conventions**:
    - **Support**: MUST be supported by all implementations, MUST NOT be `null`.
    - **Query**: MUST be a queryable property with support for all mandatory filter features.
    - **Response**: REQUIRED in the response.
    - MUST be an existing entry type.
    - The entry of type `<type>` and ID `<id>` MUST be returned in response to a request for `/<type>/<id>` under the versioned base URL.

- **Example**: `"structures"`""",
            support=SupportLevel.MUST,
            queryable=SupportLevel.MUST,
        ),
    ]

    attributes: Annotated[
        EntryResourceAttributes,
        StrictField(
            description="""A dictionary, containing key-value pairs representing the entry's properties, except for `type` and `id`.
Database-provider-specific properties need to include the database-provider-specific prefix (see section on Database-Provider-Specific Namespace Prefixes).""",
        ),
    ]

    relationships: Annotated[
        Optional[EntryRelationships],
        StrictField(
            description="""A dictionary containing references to other entries according to the description in section Relationships encoded as [JSON API Relationships](https://jsonapi.org/format/1.0/#document-resource-object-relationships).
The OPTIONAL human-readable description of the relationship MAY be provided in the `description` field inside the `meta` dictionary of the JSON API resource identifier object.""",
        ),
    ] = None


class EntryInfoProperty(BaseModel):
    description: Annotated[
        str,
        StrictField(description="A human-readable description of the entry property"),
    ]

    unit: Annotated[
        Optional[str],
        StrictField(
            description="""The physical unit of the entry property.
This MUST be a valid representation of units according to version 2.1 of [The Unified Code for Units of Measure](https://unitsofmeasure.org/ucum.html).
It is RECOMMENDED that non-standard (non-SI) units are described in the description for the property.""",
        ),
    ] = None

    sortable: Annotated[
        Optional[bool],
        StrictField(
            description="""Defines whether the entry property can be used for sorting with the "sort" parameter.
If the entry listing endpoint supports sorting, this key MUST be present for sortable properties with value `true`.""",
        ),
    ] = None

    type: Annotated[
        Optional[DataType],
        StrictField(
            title="Type",
            description="""The type of the property's value.
This MUST be any of the types defined in the Data types section.
For the purpose of compatibility with future versions of this specification, a client MUST accept values that are not `string` values specifying any of the OPTIMADE Data types, but MUST then also disregard the `type` field.
Note, if the value is a nested type, only the outermost type should be reported.
E.g., for the entry resource `structures`, the `species` property is defined as a list of dictionaries, hence its `type` value would be `list`.""",
        ),
    ] = None


class EntryInfoResource(BaseModel):
    formats: Annotated[
        list[str],
        StrictField(
            description="List of output formats available for this type of entry."
        ),
    ]

    description: Annotated[str, StrictField(description="Description of the entry.")]

    properties: Annotated[
        dict[str, EntryInfoProperty],
        StrictField(
            description="A dictionary describing queryable properties for this entry type, where each key is a property name.",
        ),
    ]

    output_fields_by_format: Annotated[
        dict[str, list[str]],
        StrictField(
            description="Dictionary of available output fields for this entry type, where the keys are the values of the `formats` list and the values are the keys of the `properties` dictionary.",
        ),
    ]
