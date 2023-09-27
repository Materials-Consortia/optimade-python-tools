# pylint: disable=line-too-long,no-self-argument
from datetime import datetime
from typing import Dict, List, Optional

from pydantic import AnyUrl, BaseModel, root_validator, validator

from optimade.models.jsonapi import Attributes, Meta, Relationships, Resource
from optimade.models.optimade_json import DataType, Relationship
from optimade.models.utils import OptimadeField, StrictField, SupportLevel

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
        if not isinstance(data, list):
            # All relationships at this point are empty-to-many relationships in JSON:API:
            # https://jsonapi.org/format/1.0/#document-resource-object-linkage
            raise ValueError("`data` key in a relationship must always store a list.")
        if hasattr(cls, "_req_type") and any(
            getattr(obj, "type", None) != cls._req_type for obj in data
        ):
            raise ValueError("Object stored in relationship data has wrong type")
        return data


class ReferenceRelationship(TypedRelationship):
    _req_type = "references"


class StructureRelationship(TypedRelationship):
    _req_type = "structures"


class TrajectoryRelationship(TypedRelationship):
    _req_type = "trajectories"


class EntryRelationships(Relationships):
    """This model wraps the JSON API Relationships to include type-specific top level keys."""

    references: Optional[ReferenceRelationship] = StrictField(
        None,
        description="Object containing links to relationships with entries of the `references` type.",
    )

    structures: Optional[StructureRelationship] = StrictField(
        None,
        description="Object containing links to relationships with entries of the `structures` type.",
    )

    trajectories: Optional[TrajectoryRelationship] = StrictField(
        None,
        description="Object containing links to relationships with entries of the `trajectories` type.",
    )


class EntryResourceAttributes(Attributes):
    """Contains key-value pairs representing the entry's properties."""

    immutable_id: Optional[str] = OptimadeField(
        None,
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
    )

    last_modified: Optional[datetime] = OptimadeField(
        ...,
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
    )

    @validator("immutable_id", pre=True)
    def cast_immutable_id_to_str(cls, value):
        """Convenience validator for casting `immutable_id` to a string."""
        if value is not None and not isinstance(value, str):
            value = str(value)

        return value


class PartialDataLink(BaseModel):
    link: AnyUrl = OptimadeField(
        ...,
        description="String. A JSON API link that points to a location from which the omitted data can be fetched. There is no requirement on the syntax or format for the link URL.",
    )
    format: str = OptimadeField(
        ...,
        description='String. The name of the format provided via this link. For one of the objects this format field SHOULD have the value "jsonlines", which refers to the format in OPTIMADE JSON lines partial data format.',
    )

    @validator("format")
    def check_if_format_is_supported(cls, value):
        from optimade.server.config import CONFIG

        if value not in [form.value for form in CONFIG.partial_data_formats]:
            raise ValueError(
                f"The format {value} is not one of the enabled_formats{CONFIG.partial_data_formats}."
            )
        return value


class EntryMetadata(Meta):
    """Contains the metadata for the attributes of an entry"""

    property_metadata: Dict = StrictField(
        None,
        description="""A dictionary, where the keys are the names of the properties in the attributes field and the value is a dictionary containing the metadata for that property.
Database-provider-specific properties need to include the database-provider-specific prefix (see section on Database-Provider-Specific Namespace Prefixes).""",
    )

    partial_data_links: Dict[str, List[PartialDataLink]] = StrictField(
        None,
        description="""A dictionary, where the keys are the names of the properties in the attributes field for which the value is too large to be shared by default.
        For each property one or more links are provided from which the value of the attribute can be retrieved.""",
    )

    @validator("property_metadata")
    def check_property_metadata_subfields(cls, property_metadata):
        from optimade.server.mappers.entries import (
            BaseResourceMapper,
        )

        if property_metadata:
            for field in property_metadata:
                if attribute_meta_dict := property_metadata.get(field):
                    for subfield in attribute_meta_dict:
                        BaseResourceMapper.check_starts_with_supported_prefix(
                            subfield,
                            "Currently no OPTIMADE fields have been defined for the per attribute metadata, thus only database and domain specific fields are allowed",
                        )
        return property_metadata

    @validator("partial_data_links")
    def check_partial_data_links_subfields(cls, partial_data_links):
        from optimade.server.mappers.entries import (
            BaseResourceMapper,
        )

        if partial_data_links:
            for field in partial_data_links:
                if attribute_partial_data_link := partial_data_links.get(field):
                    for subdict in attribute_partial_data_link:
                        for subfield in subdict.__dict__:
                            if subfield in ("link", "format"):
                                continue
                            BaseResourceMapper.check_starts_with_supported_prefix(
                                subfield,
                                "The only OPTIMADE fields defined under the 'partial_data_links' field are 'format'and ĺinks' all other database and domain specific fields must have a database/domain specific prefix.",
                            )
        return partial_data_links


class EntryResource(Resource):
    """The base model for an entry resource."""

    id: str = OptimadeField(
        ...,
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
    )

    type: str = OptimadeField(
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
    )

    attributes: EntryResourceAttributes = StrictField(
        ...,
        description="""A dictionary, containing key-value pairs representing the entry's properties, except for `type` and `id`.
Database-provider-specific properties need to include the database-provider-specific prefix (see section on Database-Provider-Specific Namespace Prefixes).""",
    )

    meta: Optional[EntryMetadata] = StrictField(
        None,
        description="""A dictionary, containing entry and property-specific metadata for a given entry.""",
    )

    relationships: Optional[EntryRelationships] = StrictField(
        None,
        description="""A dictionary containing references to other entries according to the description in section Relationships encoded as [JSON API Relationships](https://jsonapi.org/format/1.0/#document-resource-object-relationships).
The OPTIONAL human-readable description of the relationship MAY be provided in the `description` field inside the `meta` dictionary of the JSON API resource identifier object.""",
    )

    @root_validator(pre=True)
    def check_meta(cls, values):
        """Validator to check whether meta field has been formatted correctly."""
        from optimade.server.mappers.entries import (
            BaseResourceMapper,
        )

        meta = values.get("meta")
        if not meta:
            return values

        # todo the code for property_metadata and partial_data_links is very similar so it should be possible to reduce the size of the code here.
        if property_metadata := meta.pop("property_metadata", None):
            # check that all the fields under property metadata are in attributes
            attributes = values.get("attributes", {})
            for subfield in property_metadata:
                if subfield not in attributes:
                    raise ValueError(
                        f"The keys under the field `property_metadata` need to match with the field names in attributes. The field {subfield} is however not in attributes."
                    )

        if partial_data_links := meta.pop("partial_data_links", None):
            # check that all the fields under property metadata are in attributes
            attributes = values.get("attributes", {})
            for subfield in partial_data_links:
                if subfield not in attributes:
                    raise ValueError(
                        f"The keys under the field `partial_data_links` need to match with the field names in attributes. The field {subfield} is however not in attributes."
                    )

        # At this point I am getting ahead of the specification. There is the intention to allow database specific fields(with the database specific prefixes) here in line with the JSON API specification, but it has not been decided yet how this case should be handled in the property definitions.
        for field in meta:
            BaseResourceMapper.check_starts_with_supported_prefix(
                field,
                'Currently no OPTIMADE fields other than "property_metadata" have been defined for the per entry "meta" field, thus only database and domain specific fields are allowed.',
            )

        values["meta"]["property_metadata"] = property_metadata
        values["meta"]["partial_data_links"] = partial_data_links

        return values


class EntryInfoProperty(BaseModel):
    description: str = StrictField(
        ..., description="A human-readable description of the entry property"
    )

    unit: Optional[str] = StrictField(
        None,
        description="""The physical unit of the entry property.
This MUST be a valid representation of units according to version 2.1 of [The Unified Code for Units of Measure](https://unitsofmeasure.org/ucum.html).
It is RECOMMENDED that non-standard (non-SI) units are described in the description for the property.""",
    )

    sortable: Optional[bool] = StrictField(
        None,
        description="""Defines whether the entry property can be used for sorting with the "sort" parameter.
If the entry listing endpoint supports sorting, this key MUST be present for sortable properties with value `true`.""",
    )

    type: Optional[DataType] = StrictField(
        None,
        title="Type",
        description="""The type of the property's value.
This MUST be any of the types defined in the Data types section.
For the purpose of compatibility with future versions of this specification, a client MUST accept values that are not `string` values specifying any of the OPTIMADE Data types, but MUST then also disregard the `type` field.
Note, if the value is a nested type, only the outermost type should be reported.
E.g., for the entry resource `structures`, the `species` property is defined as a list of dictionaries, hence its `type` value would be `list`.""",
    )


class EntryInfoResource(BaseModel):
    formats: List[str] = StrictField(
        ..., description="List of output formats available for this type of entry."
    )

    description: str = StrictField(..., description="Description of the entry.")

    properties: Dict[str, EntryInfoProperty] = StrictField(
        ...,
        description="A dictionary describing queryable properties for this entry type, where each key is a property name.",
    )

    output_fields_by_format: Dict[str, List[str]] = StrictField(
        ...,
        description="Dictionary of available output fields for this entry type, where the keys are the values of the `formats` list and the values are the keys of the `properties` dictionary.",
    )
