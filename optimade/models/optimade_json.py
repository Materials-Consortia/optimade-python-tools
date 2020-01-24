"""Modified JSON API v1.0 for OPTiMaDe API"""
# pylint: disable=no-self-argument
from pydantic import Field, root_validator, BaseModel
from typing import Optional, Set, Union, List

from . import jsonapi


__all__ = (
    "Error",
    "Failure",
    "Success",
    "Warnings",
    "BaseRealationshipMeta",
    "BaseRelationshipResource",
    "Relationship",
)


class Error(jsonapi.Error):
    """detail MUST be present"""

    detail: str = Field(
        ...,
        description="A human-readable explanation specific to this occurrence of the problem.",
    )


class Failure(jsonapi.Response):
    """errors MUST be present and data MUST be skipped"""

    meta: Optional[jsonapi.Meta] = Field(
        None,
        description="A meta object containing non-standard information related to the Success",
    )
    errors: Set[Error] = Field(
        ...,
        description="A list of OPTiMaDe-specific JSON API error objects, where the field detail MUST be present.",
    )
    links: Optional[jsonapi.ToplevelLinks] = Field(
        None, description="Links associated with the primary data"
    )

    @root_validator(pre=True)
    def data_must_be_skipped(cls, values):
        if values.get("data", None) is not None:
            raise ValueError("data MUST be skipped for failures reporting errors")
        return values


class Success(jsonapi.Response):
    """errors are not allowed"""

    meta: Optional[jsonapi.Meta] = Field(
        None,
        description="A meta object containing non-standard information related to the Success",
    )
    links: Optional[jsonapi.ToplevelLinks] = Field(
        None, description="Links associated with the primary data"
    )

    @root_validator(pre=True)
    def either_data_meta_or_errors_must_be_set(cls, values):
        """Overwriting the existing validation function"""
        required_fields = ("data", "meta")
        if not any(values.get(field) for field in required_fields):
            raise ValueError(
                f"At least one of {required_fields} MUST be specified in the top-level response"
            )

        # errors MUST be skipped
        if values.get("errors", None) is not None:
            raise ValueError(f"'errors' MUST be skipped for a successful response")

        return values


class Warnings(Error):
    """OPTiMaDe-specific warning class based on OPTiMaDe-specific JSON API Error.
    From the specification:

        A warning resource object is defined similarly to a JSON API
        error object, but MUST also include the field type, which MUST
        have the value "warning". The field detail MUST be present and
        SHOULD contain a non-critical message, e.g., reporting
        unrecognized search attributes or deprecated features.

    Note: Must be named "Warnings", since "Warning" is a built-in Python class.
    """

    type: str = Field(
        "warning", const=True, description='Warnings must be of type "warning"'
    )

    @root_validator(pre=True)
    def status_must_not_be_specified(cls, values):
        if values.get("status", None) is not None:
            raise ValueError("status MUST NOT be specified for warnings")
        return values


class BaseRealationshipMeta(BaseModel):
    """Specific meta field for base relationship resource"""

    description: str = Field(
        ..., description="OPTIONAL human-readable description of the relationship"
    )


class BaseRelationshipResource(jsonapi.BaseResource):
    """Minimum requirements to represent a relationship resource"""

    meta: Optional[BaseRealationshipMeta] = Field(
        None,
        description="Relationship meta field. MUST contain 'description' if supplied.",
    )


class Relationship(jsonapi.Relationship):
    """Similar to normal JSON API relationship, but with addition of OPTIONAL meta field for a resource"""

    data: Optional[
        Union[BaseRelationshipResource, List[BaseRelationshipResource]]
    ] = Field(None, description="Resource linkage")
