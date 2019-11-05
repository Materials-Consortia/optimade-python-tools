from typing import Dict, List, Optional
from pydantic import BaseModel, UrlStr, Schema, validator

from .jsonapi import Resource


__all__ = ("AvailableApiVersion", "BaseInfoAttributes", "BaseInfoResource")


class AvailableApiVersion(BaseModel):
    """A JSON object containing information about an available API version"""

    url: UrlStr = Schema(
        ...,
        description="a string specifying a base URL that MUST adhere to the rules in section Base URL",
    )
    version: str = Schema(
        ...,
        description="a string containing the full version number of the API served at that base URL. "
        "The version number string MUST NOT be prefixed by, e.g., 'v'.",
    )


class BaseInfoAttributes(BaseModel):
    """Attributes for Base URL Info endpoint"""

    api_version: str = Schema(
        default="v0.10", description="Presently used version of the OPTiMaDe API"
    )
    available_api_versions: List[AvailableApiVersion] = Schema(
        ...,
        description="A list of dictionaries of available API versions at other base URLs",
    )
    formats: List[str] = Schema(
        default=["json"], description="List of available output formats."
    )
    available_endpoints: List[str] = Schema(
        default=["structures", "info"],
        description="List of available endpoints (i.e., the string to be appended to the base URL).",
    )
    entry_types_by_format: Dict[str, List[str]] = Schema(
        default={"json": ["structures"]},
        description="Available entry endpoints as a function of output formats.",
    )
    is_index: Optional[bool] = Schema(
        default=False,
        description="If true, this is an index meta-database base URL (see section Index Meta-Database). "
        "If this member is not provided, the client MUST assume this is not an index meta-database base URL "
        "(i.e., the default is for is_index to be false).",
    )

    @validator("entry_types_by_format", whole=True)
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
    id: str = Schema(default="/", const=True)
    type: str = Schema(default="info", const=True)
    attributes: BaseInfoAttributes = Schema(...)
