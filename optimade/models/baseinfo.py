# pylint: disable=no-self-argument
import re

from typing import Dict, List, Optional
from pydantic import BaseModel, AnyUrl, Field, validator

from .jsonapi import Resource


__all__ = ("AvailableApiVersion", "BaseInfoAttributes", "BaseInfoResource")


class AvailableApiVersion(BaseModel):
    """A JSON object containing information about an available API version"""

    url: AnyUrl = Field(
        ...,
        description="a string specifying a base URL that MUST adhere to the rules in section Base URL",
    )
    version: str = Field(
        ...,
        description="a string containing the full version number of the API served at that base URL. "
        "The version number string MUST NOT be prefixed by, e.g., 'v'.",
    )

    @validator("version")
    def version_must_not_prefix_v(cls, v):
        """The version number string MUST NOT be prefixed by, e.g., 'v'"""
        if not re.match(r"[0-9]+.[0-9]+(.[0-9]+)?", v):
            raise ValueError(f"version MUST NOT be prefixed by, e.g., 'v'. It is: {v}")
        return v


class BaseInfoAttributes(BaseModel):
    """Attributes for Base URL Info endpoint"""

    api_version: str = Field(
        ..., description="Presently used version of the OPTiMaDe API"
    )
    available_api_versions: List[AvailableApiVersion] = Field(
        ...,
        description="A list of dictionaries of available API versions at other base URLs",
    )
    formats: List[str] = Field(
        default=["json"], description="List of available output formats."
    )
    available_endpoints: List[str] = Field(
        ...,
        description="List of available endpoints (i.e., the string to be appended to the base URL).",
    )
    entry_types_by_format: Dict[str, List[str]] = Field(
        ..., description="Available entry endpoints as a function of output formats."
    )
    is_index: Optional[bool] = Field(
        default=False,
        description="If true, this is an index meta-database base URL (see section Index Meta-Database). "
        "If this member is not provided, the client MUST assume this is not an index meta-database base URL "
        "(i.e., the default is for is_index to be false).",
    )

    @validator("entry_types_by_format", check_fields=False)
    def formats_and_endpoints_must_be_valid(cls, v, values):
        for format_, endpoints in v.items():
            if format_ not in values["formats"]:
                raise ValueError(f"'{format_}' must be listed in formats to be valid")
            for endpoint in endpoints:
                if endpoint not in values["available_endpoints"]:
                    raise ValueError(
                        f"'{endpoint}' must be listed in available_endpoints to be valid"
                    )
        return v


class BaseInfoResource(Resource):
    id: str = Field(default="/", const=True)
    type: str = Field(default="info", const=True)
    attributes: BaseInfoAttributes = Field(...)
