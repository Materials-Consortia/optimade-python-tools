# pylint: disable=line-too-long,no-self-argument
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, validator  # pylint: disable=no-name-in-module

from optimade.models.jsonapi import Attributes, Relationships, Resource
from optimade.models.optimade_json import AllowedJSONSchemaDataType, Relationship
from optimade.models.utils import OptimadeField, QuerySupport, StrictField, SupportLevel

__all__ = (
    "EntryRelationships",
    "EntryResourceAttributes",
    "EntryResource",
    "EntryInfoProperty",
    "EntryInfoResource",
)


class OptimadeAllowedUnitStandard(Enum):
    GNU_UNITS = "gnu units"
    UCUM = "ucum"
    QUDT = "qudt"


class UnitResourceURIs(BaseModel):
    relation: str
    uri: str


class OptimadeUnitStandard(BaseModel):
    name: OptimadeAllowedUnitStandard
    version: str
    symbol: str


class OptimadeUnitDefinition(BaseModel):
    symbol: str
    title: str
    description: str
    standard: OptimadeUnitStandard
    resource_uris: Optional[List[UnitResourceURIs]] = StrictField(
        ..., alias="resource-uris"
    )


class JSONSchemaObject(BaseModel):

    properties: Dict[str, "EntryInfoProperty"] = StrictField(
        ...,
        description="""Gives key-value pairs where each value is an inner Property Definition.
The defined property is a dictionary that can only contain keys present in this dictionary, and, if so, the corresponding value is described by the respective inner Property Definition.
(Or, if the `type` field is the list "object" and "null", it can also be `null`.)""",
    )

    required: Optional[List[str]] = StrictField(
        ...,
        description="""The list MUST only contain strings.

The defined property MUST have keys that match all the strings in this list.
Other keys present in the `properties` field are OPTIONAL in the defined property.
If not present or empty, all keys in `properties` are regarded as OPTIONAL.""",
    )
    maxProperties: Optional[int]
    minProperties: Optional[int]
    dependentRequired: Optional[Dict]


class JSONSchemaArray(BaseModel):
    items: "EntryInfoProperty" = StrictField(...)
    maxItems: Optional[int]
    minItems: Optional[int]
    uniqueItems: Optional[bool]


class JSONSchemaInteger(BaseModel):
    multipleOf: Optional[int]
    maximum: Optional[int]
    exclusiveMaximum: Optional[int]
    minimum: Optional[int]
    exclusiveMinimum: Optional[int]


class JSONSchemaNumber(BaseModel):
    multipleOf: Optional[float]
    maximum: Optional[float]
    exclusiveMaximum: Optional[float]
    minimum: Optional[float]
    exclusiveMinimum: Optional[float]


class JSONSchemaStringFormat(Enum):
    DATETIME = "date-time"
    DATE = "date"
    TIME = "time"
    DURATION = "duration"
    EMAIL = "email"
    URI = "uri"


class JSONSchemaString(BaseModel):
    maxLength: Optional[int]
    minLength: Optional[int]
    format: Optional[JSONSchemaStringFormat]


class PropertyImplementationInfo(BaseModel):

    sortable: Optional[bool] = StrictField(
        ...,
        description="""If `TRUE`, specifies that results can be sorted on this property.
    If `FALSE`, specifies that results cannot be sorted on this property.
    Omitting the field is equivalent to `FALSE`.""",
    )

    query_support: Optional[QuerySupport] = StrictField(
        ...,
        alias="query-support",
        description="""Defines a required level of support in formulating queries on this field.

    The string MUST be one of the following:

    - `all mandatory`: the defined property MUST be queryable using the OPTIMADE filter language with support for all mandatory filter features.
    - `equality only`: the defined property MUST be queryable using the OPTIMADE filter language equality and inequality operators. Other filter language features do not need to be available.
    - `partial`: the defined property MUST be queryable with support for a subset of the filter language operators as specified by the field `query-support-operators`.
    - `none`: the defined property does not need to be queryable with any features of the filter language.""",
    )

    query_support_operators: Optional[List[str]] = StrictField(
        ...,
        alias="query-support-operators",
        description="""Defines the filter language features supported on this property.

Each string in the list MUST be one of `<`, `<=`, `>`, `>=`, `=`, `!=`, `CONTAINS`, `STARTS WITH`, `ENDS WITH`:, `HAS`, `HAS ALL`, `HAS ANY`, `HAS ONLY`, `IS KNOWN`, `IS UNKNOWN` with the following meanings:

- `<`, `<=`, `>`, `>=`, `=`, `!=`: indicating support for filtering this property using the respective operator.
  If the property is of Boolean type, support for `=` also designates support for boolean comparisons with the property being true that omit ":filter-fragment:`= TRUE`", e.g., specifying that filtering for "`is_yellow = TRUE`" is supported also implies support for "`is_yellow`" (which means the same thing).
  Support for "`NOT is_yellow`" also follows.

- `CONTAINS`, `STARTS WITH`, `ENDS WITH`: indicating support for substring filtering of this property using the respective operator. MUST NOT appear if the property is not of type String.

- `HAS`, `HAS ALL`, `HAS ANY`: indicating support of the MANDATORY features for list property comparison using the respective operator. MUST NOT appear if the property is not of type List.

- `HAS ONLY`: indicating support for list property comparison with all or a subset of the OPTIONAL constructs using this operator. MUST NOT appear if the property is not of type List.

- `IS KNOWN`, `IS UNKNOWN`: indicating support for filtering this property on unknown values using the respective operator.""",
    )


class PropertyRequirementsInfo(PropertyImplementationInfo):
    support: SupportLevel = StrictField(
        ...,
        description="""Describes the minimal required level of support for the Property by an implementation.

    This field SHOULD only appear in a `x-optimade-requirements` that is at the outermost level of a Property Definition, as the meaning of its inclusion on other levels is not defined.
    The string MUST be one of the following:

    - `must`: the defined property MUST be recognized by the implementation (e.g., in filter strings) and MUST NOT be `null`.
    - `should`: the defined property MUST be recognized by the implementation (e.g., in filter strings) and SHOULD NOT be `null`.
    - `may`: it is OPTIONAL for the implementation to recognize the defined property and it MAY be equal to `null`.""",
    )


class PropertyRemoteResource(BaseModel):

    relation: str = StrictField(
        ...,
        description="A human-readable description of the relationship between the property and the remote resource, e.g., a 'natural language description'.",
    )

    uri: str = StrictField(
        ...,
        description="A URI of the external resource (which MAY be a resolvable URL).",
    )


class OptimadePropertyDefinition(BaseModel):

    property_uri: str = StrictField(
        ...,
        alias="property-uri",
        description="""A static URI identifier that is a URN or URL representing the specific version of the property.
It SHOULD NOT be changed as long as the property definition remains the same, and SHOULD be changed when the property definition changes.
(If it is a URL, clients SHOULD NOT assign any interpretation to the response when resolving that URL.)""",
    )

    version: Optional[str] = StrictField(
        ...,
        description="""This string indicates the version of the property definition.
The string SHOULD be in the format described by the [semantic versioning v2](https://semver.org/spec/v2.0.0.html) standard.""",
    )

    unit_definitions: Optional[List[OptimadeUnitDefinition]] = StrictField(
        ...,
        alias="unit-definitions",
        description="""A list of definitions of the symbols used in the Property Definition (including its nested levels) for physical units given as values of the `x-optimade-unit` field.
This field MUST be included if the defined property, at any level, includes an `x-optimade-unit` with a value that is not `dimensionless` or `inapplicable`.""",
    )

    resource_uris: Optional[List[PropertyRemoteResource]] = StrictField(
        ...,
        alias="resource-uris",
        description="A list of dictionaries that references remote resources that describe the property.",
    )


class TypedRelationship(Relationship):
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

    relationships: Optional[EntryRelationships] = StrictField(
        None,
        description="""A dictionary containing references to other entries according to the description in section Relationships encoded as [JSON API Relationships](https://jsonapi.org/format/1.0/#document-resource-object-relationships).
The OPTIONAL human-readable description of the relationship MAY be provided in the `description` field inside the `meta` dictionary of the JSON API resource identifier object.""",
    )


class EntryInfoProperty(BaseModel):

    title: str = StrictField(
        ...,
        description="A short single-line human-readable explanation of the defined property appropriate to show as part of a user interface.",
    )

    description: str = StrictField(
        ...,
        description="""A human-readable multi-line description that explains the purpose, requirements, and conventions of the defined property.

The format SHOULD be a one-line description, followed by a new paragraph (two newlines), followed by a more detailed description of all the requirements and conventions of the defined property.
Formatting in the text SHOULD use Markdown in the CommonMark v0.3 format.""",
    )

    property: OptimadePropertyDefinition = StrictField(
        ...,
        alias="x-optimade-property",
        description="Additional information to define the property that is not covered by fields in the JSON Schema standard.",
    )

    unit: Optional[str] = StrictField(
        None,
        alias="x-optimade-unit",
        description="A (compound) symbol for the physical unit in which the value of the defined property is given or one of the strings `dimensionless` or `inapplicable`.",
    )

    implementation: Optional[PropertyImplementationInfo] = StrictField(
        ...,
        alias="x-optimade-implementation",
        description="""A dictionary describing the level of OPTIMADE API functionality provided by the present implementation.
If an implementation omits this field in its response, a client interacting with that implementation SHOULD NOT make any assumptions about the availability of these features.""",
    )

    requirements: Optional[PropertyRequirementsInfo] = StrictField(
        ...,
        alias="x-optimade-requirements",
        description="""A dictionary describing the level of OPTIMADE API functionality required by all implementations of this property.
Omitting this field means the corresponding functionality is OPTIONAL.""",
    )

    type: Union[
        AllowedJSONSchemaDataType, List[AllowedJSONSchemaDataType]
    ] = StrictField(
        None,
        title="Type",
        description="""A string or list that specifies the type of the defined property.
It MUST be one of:

- One of the strings `"boolean"`, `"object"` (refers to an OPTIMADE dictionary), `"array"` (refers to an OPTIMADE list), `"number"` (refers to an OPTIMADE float), `"string"`, or `"integer"`.
- A list where the first item MUST be one of the strings above, and the second item MUST be the string `"null"`.""",
    )

    deprecated: Optional[bool] = StrictField(
        ...,
        description=""" If `TRUE`, implementations SHOULD not use the defined property, and it MAY be removed in the future.
If `FALSE`, the defined property is not deprecated.
The field not being present means `FALSE`.""",
    )

    enum: Optional[List] = StrictField(
        ...,
        description="""The defined property MUST take one of the values given in the provided list.
The items in the list MUST all be of a data type that matches the `type` field and otherwise adhere to the rest of the Property Description.
If this key is given, for `null` to be a valid value of the defined property, the list MUST contain a `null` value and the `type` MUST be a list where the second value is the string `"null"`.""",
    )

    examples: Optional[List] = StrictField(
        ...,
        description="""A list of example values that the defined property can have.
These examples MUST all be of a data type that matches the `type` field and otherwise adhere to the rest of the Property Description.""",
    )


class EntryInfoPropertyObject(EntryInfoProperty, JSONSchemaObject):
    ...


class EntryInfoPropertyArray(EntryInfoProperty, JSONSchemaArray):
    ...


class EntryInfoPropertyNumber(EntryInfoProperty, JSONSchemaInteger):
    ...


class EntryInfoPropertyString(EntryInfoProperty, JSONSchemaString):
    ...


class EntryInfoPropertyInteger(EntryInfoProperty, JSONSchemaInteger):
    ...


class EntryInfoResource(BaseModel):

    formats: List[str] = StrictField(
        ..., description="List of output formats available for this type of entry."
    )

    description: str = StrictField(..., description="Description of the entry.")

    properties: Dict[
        str,
        Union[
            EntryInfoProperty,
            EntryInfoPropertyArray,
            EntryInfoPropertyInteger,
            EntryInfoPropertyNumber,
            EntryInfoPropertyObject,
            EntryInfoPropertyString,
        ],
    ] = StrictField(
        ...,
        description="A dictionary describing queryable properties for this entry type, where each key is a property name.",
    )

    output_fields_by_format: Dict[str, List[str]] = StrictField(
        ...,
        description="Dictionary of available output fields for this entry type, where the keys are the values of the `formats` list and the values are the keys of the `properties` dictionary.",
    )
