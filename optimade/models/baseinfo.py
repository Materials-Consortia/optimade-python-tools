import re
from typing import Annotated, Literal, Optional

from pydantic import AnyHttpUrl, BaseModel, field_validator, model_validator

from optimade.models.jsonapi import Resource
from optimade.models.types import SemanticVersion
from optimade.models.utils import StrictField

__all__ = ("AvailableApiVersion", "BaseInfoAttributes", "BaseInfoResource")


VERSIONED_BASE_URL_PATTERN = r"^.+/v[0-1](\.[0-9]+)*/?$"


class AvailableApiVersion(BaseModel):
    """A JSON object containing information about an available API version"""

    url: Annotated[
        AnyHttpUrl,
        StrictField(
            description="A string specifying a versioned base URL that MUST adhere to the rules in section Base URL",
            json_schema_extra={
                "pattern": VERSIONED_BASE_URL_PATTERN,
            },
        ),
    ]

    version: Annotated[
        SemanticVersion,
        StrictField(
            description="""A string containing the full version number of the API served at that versioned base URL.
The version number string MUST NOT be prefixed by, e.g., 'v'.
Examples: `1.0.0`, `1.0.0-rc.2`.""",
        ),
    ]

    @field_validator("url", mode="after")
    @classmethod
    def url_must_be_versioned_base_Url(cls, value: AnyHttpUrl) -> AnyHttpUrl:
        """The URL must be a versioned base URL"""
        if not re.match(VERSIONED_BASE_URL_PATTERN, str(value)):
            raise ValueError(
                f"URL {value} must be a versioned base URL (i.e., must match the "
                f"pattern '{VERSIONED_BASE_URL_PATTERN}')"
            )
        return value

    @model_validator(mode="after")
    def crosscheck_url_and_version(self) -> "AvailableApiVersion":
        """Check that URL version and API version are compatible."""
        url = (
            str(self.url)
            .split("/")[-2 if str(self.url).endswith("/") else -1]
            .replace("v", "")
        )
        # as with version urls, we need to split any release tags or build metadata out of these URLs
        url_version = tuple(
            int(val) for val in url.split("-")[0].split("+")[0].split(".")
        )
        api_version = tuple(
            int(val) for val in str(self.version).split("-")[0].split("+")[0].split(".")
        )
        if any(a != b for a, b in zip(url_version, api_version)):
            raise ValueError(
                f"API version {api_version} is not compatible with url version {url_version}."
            )
        return self


class BaseInfoAttributes(BaseModel):
    """Attributes for Base URL Info endpoint"""

    api_version: Annotated[
        SemanticVersion,
        StrictField(
            description="""Presently used full version of the OPTIMADE API.
The version number string MUST NOT be prefixed by, e.g., "v".
Examples: `1.0.0`, `1.0.0-rc.2`.""",
        ),
    ]
    available_api_versions: Annotated[
        list[AvailableApiVersion],
        StrictField(
            description="A list of dictionaries of available API versions at other base URLs",
        ),
    ]
    formats: Annotated[
        list[str], StrictField(description="List of available output formats.")
    ] = ["json"]
    available_endpoints: Annotated[
        list[str],
        StrictField(
            description="List of available endpoints (i.e., the string to be appended to the versioned base URL).",
        ),
    ]
    entry_types_by_format: Annotated[
        dict[str, list[str]],
        StrictField(
            description="Available entry endpoints as a function of output formats."
        ),
    ]
    is_index: Annotated[
        Optional[bool],
        StrictField(
            description="If true, this is an index meta-database base URL (see section Index Meta-Database). "
            "If this member is not provided, the client MUST assume this is not an index meta-database base URL "
            "(i.e., the default is for `is_index` to be `false`).",
        ),
    ] = False

    @model_validator(mode="after")
    def formats_and_endpoints_must_be_valid(self) -> "BaseInfoAttributes":
        for format_, endpoints in self.entry_types_by_format.items():
            if format_ not in self.formats:
                raise ValueError(f"'{format_}' must be listed in formats to be valid")
            for endpoint in endpoints:
                if endpoint not in self.available_endpoints:
                    raise ValueError(
                        f"'{endpoint}' must be listed in available_endpoints to be valid"
                    )
        return self


class BaseInfoResource(Resource):
    id: Literal["/"] = "/"
    type: Literal["info"] = "info"
    attributes: BaseInfoAttributes
