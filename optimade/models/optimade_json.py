"""Modified JSON API v1.0 for OPTiMaDe API"""
from pydantic import Field, validator
from typing import Optional, Set

from . import jsonapi


__all__ = ("Error", "Failure", "Success", "Warnings")


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

    @validator("data")
    def data_must_be_skipped(cls, v):
        raise ValueError("data MUST be skipped for failures reporting errors")


class Success(jsonapi.Response):
    """errors are not allowed"""

    meta: Optional[jsonapi.Meta] = Field(
        None,
        description="A meta object containing non-standard information related to the Success",
    )
    links: Optional[jsonapi.ToplevelLinks] = Field(
        None, description="Links associated with the primary data"
    )

    @validator("meta", always=True)
    def either_data_or_meta_must_be_set(cls, v, values):
        if values.get("data", None) is None and v is None:
            raise ValueError("Either 'data' or 'meta' must be specified")
        return v

    @validator("errors")
    def either_data_meta_or_errors_must_be_set(cls, v, values):
        """Overwriting the existing validation function"""
        raise ValueError("'errors' MUST be skipped for a successful response")


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

    @validator("status")
    def status_must_not_be_specified(cls, v):
        raise ValueError("status MUST NOT be specified for warnings")
