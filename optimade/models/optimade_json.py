"""Modified JSON API v1.0 for OPTIMADE API"""

from datetime import datetime
from enum import Enum
from typing import Annotated, Any, Literal, Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    NonNegativeFloat,
    model_validator,
)

from optimade.models import jsonapi
from optimade.models.types import SemanticVersion
from optimade.models.utils import IDENTIFIER_REGEX, StrictField

__all__ = (
    "DataType",
    "ResponseMetaQuery",
    "Provider",
    "ImplementationMaintainer",
    "Implementation",
    "ResponseMeta",
    "OptimadeError",
    "Success",
    "Warnings",
    "BaseRelationshipMeta",
    "BaseRelationshipResource",
    "Relationship",
)

ValidIdentifier = Annotated[str, Field(pattern=IDENTIFIER_REGEX)]
"""A type that constrains strings to valid OPTIMADE identifiers (e.g., property names, ID strings)."""


class DataType(Enum):
    """Optimade Data types

    See the section "Data types" in the OPTIMADE API specification for more information.
    """

    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    TIMESTAMP = "timestamp"
    LIST = "list"
    DICTIONARY = "dictionary"
    UNKNOWN = "unknown"

    @classmethod
    def get_values(cls) -> list[str]:
        """Get OPTIMADE data types (enum values) as a (sorted) list"""
        return sorted(_.value for _ in cls)

    @classmethod
    def from_python_type(cls, python_type: type | str | object) -> Optional["DataType"]:
        """Get OPTIMADE data type from a Python type"""
        mapping = {
            "bool": cls.BOOLEAN,
            "int": cls.INTEGER,
            "float": cls.FLOAT,
            "complex": None,
            "generator": cls.LIST,
            "list": cls.LIST,
            "tuple": cls.LIST,
            "range": cls.LIST,
            "hash": cls.INTEGER,
            "str": cls.STRING,
            "bytes": cls.STRING,
            "bytearray": None,
            "memoryview": None,
            "set": cls.LIST,
            "frozenset": cls.LIST,
            "dict": cls.DICTIONARY,
            "dict_keys": cls.LIST,
            "dict_values": cls.LIST,
            "dict_items": cls.LIST,
            "Nonetype": cls.UNKNOWN,
            "None": cls.UNKNOWN,
            "datetime": cls.TIMESTAMP,
            "date": cls.TIMESTAMP,
            "time": cls.TIMESTAMP,
            "datetime.datetime": cls.TIMESTAMP,
            "datetime.date": cls.TIMESTAMP,
            "datetime.time": cls.TIMESTAMP,
        }

        if isinstance(python_type, type):
            python_type = python_type.__name__
        elif isinstance(python_type, object):
            if str(python_type) in mapping:
                python_type = str(python_type)
            else:
                python_type = type(python_type).__name__

        return mapping.get(python_type, None)

    @classmethod
    def from_json_type(cls, json_type: str) -> Optional["DataType"]:
        """Get OPTIMADE data type from a named JSON type"""
        mapping = {
            "string": cls.STRING,
            "integer": cls.INTEGER,
            "number": cls.FLOAT,  # actually includes both integer and float
            "object": cls.DICTIONARY,
            "array": cls.LIST,
            "boolean": cls.BOOLEAN,
            "null": cls.UNKNOWN,
            # OpenAPI "format"s:
            "double": cls.FLOAT,
            "float": cls.FLOAT,
            "int32": cls.INTEGER,
            "int64": cls.INTEGER,
            "date": cls.TIMESTAMP,
            "date-time": cls.TIMESTAMP,
            "password": cls.STRING,
            "byte": cls.STRING,
            "binary": cls.STRING,
            # Non-OpenAPI "format"s, but may still be used by pydantic/FastAPI
            "email": cls.STRING,
            "uuid": cls.STRING,
            "uri": cls.STRING,
            "hostname": cls.STRING,
            "ipv4": cls.STRING,
            "ipv6": cls.STRING,
        }

        return mapping.get(json_type, None)


class OptimadeError(jsonapi.Error):
    """detail MUST be present"""

    detail: Annotated[
        str,
        StrictField(
            description="A human-readable explanation specific to this occurrence of the problem.",
        ),
    ]


def warnings_json_schema_extra(schema: dict[str, Any], model: type["Warnings"]) -> None:
    """Update OpenAPI JSON schema model for `Warning`.

    * Ensure `type` is in the list required properties and in the correct place.
    * Remove `status` property.
        This property is not allowed for `Warning`, nor is it a part of the OPTIMADE
        definition of the `Warning` object.

    Note:
        Since `type` is the _last_ model field defined, it will simply be appended.

    """
    if "required" in schema:
        if "type" not in schema["required"]:
            schema["required"].append("type")
        else:
            schema["required"] = ["type"]
    schema.get("properties", {}).pop("status", None)


class Warnings(OptimadeError):
    """OPTIMADE-specific warning class based on OPTIMADE-specific JSON API Error.

    From the specification:

    A warning resource object is defined similarly to a JSON API error object, but MUST also include the field type, which MUST have the value "warning".
    The field detail MUST be present and SHOULD contain a non-critical message, e.g., reporting unrecognized search attributes or deprecated features.

    Note: Must be named "Warnings", since "Warning" is a built-in Python class.

    """

    model_config = ConfigDict(json_schema_extra=warnings_json_schema_extra)

    type: Annotated[
        Literal["warning"],
        StrictField(
            description='Warnings must be of type "warning"',
            pattern="^warning$",
        ),
    ] = "warning"

    @model_validator(mode="after")
    def status_must_not_be_specified(self) -> "Warnings":
        if self.status or "status" in self.model_fields_set:
            raise ValueError("status MUST NOT be specified for warnings")
        return self


class ResponseMetaQuery(BaseModel):
    """Information on the query that was requested."""

    representation: Annotated[
        str,
        StrictField(
            description="""A string with the part of the URL following the versioned or unversioned base URL that serves the API.
Query parameters that have not been used in processing the request MAY be omitted.
In particular, if no query parameters have been involved in processing the request, the query part of the URL MAY be excluded.
Example: `/structures?filter=nelements=2`""",
        ),
    ]


class Provider(BaseModel):
    """Information on the database provider of the implementation."""

    name: Annotated[
        str, StrictField(description="a short name for the database provider")
    ]

    description: Annotated[
        str, StrictField(description="a longer description of the database provider")
    ]

    prefix: Annotated[
        str,
        StrictField(
            pattern=r"^[a-z]([a-z]|[0-9]|_)*$",
            description="database-provider-specific prefix as found in section Database-Provider-Specific Namespace Prefixes.",
        ),
    ]

    homepage: Annotated[
        jsonapi.JsonLinkType | None,
        StrictField(
            description="a [JSON API links object](http://jsonapi.org/format/1.0#document-links) "
            "pointing to homepage of the database provider, either "
            "directly as a string, or as a link object.",
        ),
    ] = None


class ImplementationMaintainer(BaseModel):
    """Details about the maintainer of the implementation"""

    email: Annotated[
        EmailStr, StrictField(description="the maintainer's email address")
    ]


class Implementation(BaseModel):
    """Information on the server implementation"""

    name: Annotated[
        str | None, StrictField(description="name of the implementation")
    ] = None

    version: Annotated[
        str | None,
        StrictField(description="version string of the current implementation"),
    ] = None

    homepage: Annotated[
        jsonapi.JsonLinkType | None,
        StrictField(
            description="A [JSON API links object](http://jsonapi.org/format/1.0/#document-links) pointing to the homepage of the implementation.",
        ),
    ] = None

    source_url: Annotated[
        jsonapi.JsonLinkType | None,
        StrictField(
            description="A [JSON API links object](http://jsonapi.org/format/1.0/#document-links) pointing to the implementation source, either downloadable archive or version control system.",
        ),
    ] = None

    maintainer: Annotated[
        ImplementationMaintainer | None,
        StrictField(
            description="A dictionary providing details about the maintainer of the implementation.",
        ),
    ] = None

    issue_tracker: Annotated[
        jsonapi.JsonLinkType | None,
        StrictField(
            description="A [JSON API links object](http://jsonapi.org/format/1.0/#document-links) pointing to the implementation's issue tracker.",
        ),
    ] = None


class ResponseMeta(jsonapi.Meta):
    """
    A [JSON API meta member](https://jsonapi.org/format/1.0#document-meta)
    that contains JSON API meta objects of non-standard
    meta-information.

    OPTIONAL additional information global to the query that is not
    specified in this document, MUST start with a
    database-provider-specific prefix.
    """

    query: Annotated[
        ResponseMetaQuery,
        StrictField(description="Information on the Query that was requested"),
    ]

    api_version: Annotated[
        SemanticVersion,
        StrictField(
            description="""Presently used full version of the OPTIMADE API.
The version number string MUST NOT be prefixed by, e.g., "v".
Examples: `1.0.0`, `1.0.0-rc.2`.""",
        ),
    ]

    more_data_available: Annotated[
        bool,
        StrictField(
            description="`false` if the response contains all data for the request (e.g., a request issued to a single entry endpoint, or a `filter` query at the last page of a paginated response) and `true` if the response is incomplete in the sense that multiple objects match the request, and not all of them have been included in the response (e.g., a query with multiple pages that is not at the last page).",
        ),
    ]

    # start of "SHOULD" fields for meta response
    optimade_schema: Annotated[
        jsonapi.JsonLinkType | None,
        StrictField(
            alias="schema",
            description="""A [JSON API links object](http://jsonapi.org/format/1.0/#document-links) that points to a schema for the response.
If it is a string, or a dictionary containing no `meta` field, the provided URL MUST point at an [OpenAPI](https://swagger.io/specification/) schema.
It is possible that future versions of this specification allows for alternative schema types.
Hence, if the `meta` field of the JSON API links object is provided and contains a field `schema_type` that is not equal to the string `OpenAPI` the client MUST not handle failures to parse the schema or to validate the response against the schema as errors.""",
        ),
    ] = None

    time_stamp: Annotated[
        datetime | None,
        StrictField(
            description="A timestamp containing the date and time at which the query was executed.",
        ),
    ] = None

    data_returned: Annotated[
        int | None,
        StrictField(
            description="An integer containing the total number of data resource objects returned for the current `filter` query, independent of pagination.",
            ge=0,
        ),
    ] = None

    provider: Annotated[
        Provider | None,
        StrictField(
            description="information on the database provider of the implementation."
        ),
    ] = None

    # start of "MAY" fields for meta response
    data_available: Annotated[
        int | None,
        StrictField(
            description="An integer containing the total number of data resource objects available in the database for the endpoint.",
        ),
    ] = None

    last_id: Annotated[
        str | None,
        StrictField(description="a string containing the last ID returned"),
    ] = None

    response_message: Annotated[
        str | None, StrictField(description="response string from the server")
    ] = None

    request_delay: Annotated[
        NonNegativeFloat | None,
        StrictField(
            description="""A non-negative float giving time in seconds that the client is suggested to wait before issuing a subsequent request.
Implementation note: the functionality of this field overlaps to some degree with features provided by the HTTP error `429 Too Many Requests` and the `Retry-After` HTTP header.
Implementations are suggested to provide consistent handling of request overload through both mechanisms."""
        ),
    ] = None

    implementation: Annotated[
        Implementation | None,
        StrictField(description="a dictionary describing the server implementation"),
    ] = None

    warnings: Annotated[
        list[Warnings] | None,
        StrictField(
            description="""A list of warning resource objects representing non-critical errors or warnings.
A warning resource object is defined similarly to a [JSON API error object](http://jsonapi.org/format/1.0/#error-objects), but MUST also include the field `type`, which MUST have the value `"warning"`.
The field `detail` MUST be present and SHOULD contain a non-critical message, e.g., reporting unrecognized search attributes or deprecated features.
The field `status`, representing a HTTP response status code, MUST NOT be present for a warning resource object.
This is an exclusive field for error resource objects.""",
            uniqueItems=True,
        ),
    ] = None


class Success(jsonapi.Response):
    """errors are not allowed"""

    meta: Annotated[
        ResponseMeta,
        StrictField(description="A meta object containing non-standard information"),
    ]

    @model_validator(mode="after")
    def either_data_meta_or_errors_must_be_set(self) -> "Success":
        """Overwriting the existing validation function, since 'errors' MUST NOT be set."""
        required_fields = ("data", "meta")
        if not any(field in self.model_fields_set for field in required_fields):
            raise ValueError(
                f"At least one of {required_fields} MUST be specified in the top-level response."
            )

        # errors MUST be skipped
        if self.errors or "errors" in self.model_fields_set:
            raise ValueError("'errors' MUST be skipped for a successful response.")

        return self


class BaseRelationshipMeta(jsonapi.Meta):
    """Specific meta field for base relationship resource"""

    description: Annotated[
        str,
        StrictField(
            description="OPTIONAL human-readable description of the relationship."
        ),
    ]


class BaseRelationshipResource(jsonapi.BaseResource):
    """Minimum requirements to represent a relationship resource"""

    meta: Annotated[
        BaseRelationshipMeta | None,
        StrictField(
            description="Relationship meta field. MUST contain 'description' if supplied.",
        ),
    ] = None


class Relationship(jsonapi.Relationship):
    """Similar to normal JSON API relationship, but with addition of OPTIONAL meta field for a resource."""

    data: Annotated[
        BaseRelationshipResource | list[BaseRelationshipResource] | None,
        StrictField(description="Resource linkage", uniqueItems=True),
    ] = None
