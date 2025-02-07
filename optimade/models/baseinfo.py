import re
from typing import Annotated, Literal

from pydantic import AnyHttpUrl, BaseModel, field_validator, model_validator

from optimade.models.jsonapi import Link, Resource
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
        bool | None,
        StrictField(
            description="If true, this is an index meta-database base URL (see section Index Meta-Database). "
            "If this member is not provided, the client MUST assume this is not an index meta-database base URL "
            "(i.e., the default is for `is_index` to be `false`).",
        ),
    ] = False
    license: Annotated[
        Link | AnyHttpUrl | None,
        StrictField(
            ...,
            description="""A [JSON API links object](http://jsonapi.org/format/1.0/#document-links) giving a URL to a web page containing a human-readable text describing the license (or licensing options if there are multiple) covering all the data and metadata provided by this database.
Clients are advised not to try automated parsing of this link or its content, but rather rely on the field `available_licenses` instead.""",
        ),
    ] = None
    available_licenses: Annotated[
        list[str] | None,
        StrictField(
            ...,
            description="""List of [SPDX license identifiers](https://spdx.org/licenses/) specifying a set of alternative licenses available to the client for licensing the complete database, i.e., all the entries, metadata, and the content and structure of the database itself.

If more than one license is available to the client, the identifier of each one SHOULD be included in the list.
Inclusion of a license identifier in the list is a commitment of the database that the rights are in place to grant clients access to all the individual entries, all metadata, and the content and structure of the database itself according to the terms of any of these licenses (at the choice of the client).
If the licensing information provided via the field license omits licensing options specified in `available_licenses`, or if it otherwise contradicts them, a client MUST still be allowed to interpret the inclusion of a license in `available_licenses` as a full commitment from the database without exceptions, under the respective licenses.
If the database cannot make that commitment, e.g., if only part of the database is available under a license, the corresponding license identifier MUST NOT appear in `available_licenses` (but, rather, the field license is to be used to clarify the licensing situation.)
An empty list indicates that none of the SPDX licenses apply and that the licensing situation is clarified in human readable form in the field `license`.
An unknown value means that the database makes no commitment.""",
        ),
    ] = None

    available_licenses_for_entries: Annotated[
        list[str] | None,
        StrictField(
            ...,
            description="""List of [SPDX license identifiers](https://spdx.org/licenses/) specifying a set of additional alternative licenses available to the client for licensing individual, and non-substantial sets of, database entries, metadata, and extracts from the database that do not constitute substantial parts of the database.

Note that the definition of the field `available_licenses` implies that licenses specified in that field are available also for the licensing specified by this field, even if they are not explicitly included in the field `available_licenses_for_entries` or if it is `null` (however, the opposite relationship does not hold).
If `available_licenses` is unknown, only the licenses in `available_licenses_for_entries` apply.""",
        ),
    ] = None

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
