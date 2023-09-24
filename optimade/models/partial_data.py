from typing import Literal, Optional

from pydantic import BaseModel

from optimade.models.entries import EntryResource
from optimade.models.utils import OptimadeField, StrictField, SupportLevel

__all__ = ("PartialDataHeader", "PartialDataResource", "LinksObject")


class LinksObject(BaseModel):
    base_url: Optional[str] = OptimadeField(
        None,
        description="""The base URL of the implementation serving the database to which this property belongs.""",
    )
    item_describedby: Optional[
        str
    ] = OptimadeField(  # The term describedby is used in the json Api, therefore we do not place an underscore between described and by.
        None,
        description="""A URL to an external JSON Schema that validates the data lines of the response.
    The format and requirements on this schema are the same as for the inline schema field :field:`item_schema`.
The format of data lines of the response (i.e., all lines except the first and the last) depends on whether the header object specifies the layout as :val:`"dense"` or :val:`"sparse"`.
""",
    )


class PartialDataInfo(BaseModel):
    version: str = OptimadeField(
        ...,
        description="""Specifies the minor version of the partial data format used.
    The string MUST be of the format "MAJOR.MINOR", referring to the version of the OPTIMADE standard that describes the format.
    The version number string MUST NOT be prefixed by, e.g., "v". In implementations of the present version of the standard, the value MUST be exactly :val:`1.2`.
    A client MUST NOT expect to be able to parse the :field:`format` value if the field is not a string of the format MAJOR.MINOR or if the MAJOR version number is unrecognized.""",
    )


class PartialDataHeader(BaseModel):
    optimade_partial_data: PartialDataInfo = OptimadeField(
        ...,
        description="""An object identifying the response as being on OPTIMADE partial data format.
It MUST contain the following key:
"version": String. Specifies the minor version of the partial data format used. The string MUST be of the format "MAJOR.MINOR", referring to the version of the OPTIMADE standard that describes the format. The version number string MUST NOT be prefixed by, e.g., "v". In implementations of the present version of the standard, the value MUST be exactly 1.2. A client MUST NOT expect to be able to parse the version value if the field is not a string of the format MAJOR.MINOR or if the MAJOR version number is unrecognized.

- **Type**: Dictionary.

- **Requirements/Conventions**:
    - **Support**: MUST be supported by all implementations, MUST NOT be `null`.

- **Examples**:
    - `""optimade-partial-data": {"version": "1.2.0"}"`""",
        support=SupportLevel.MUST,
    )
    layout: Literal["dense", "sparse"] = OptimadeField(
        ...,
        description="""A string either equal to "dense" or "sparse" to indicate whether the returned format uses a dense or sparse layout.

- **Type**: string.

- **Requirements/Conventions**:
    - **Support**: MUST be supported by all implementations, MUST NOT be `null`.

- **Examples**:
    - `"dense"`
    - `"sparse"`""",
        support=SupportLevel.MUST,
    )
    returned_ranges: Optional[list[dict]] = OptimadeField(
        None,
        description="""Array of Objects. For dense layout, and sparse layout of one dimensional list properties, the array contains a single element which is a slice object representing the range of data present in the response. In the specific case of a hierarchy of list properties represented as a sparse multi-dimensional array, if the field "returned_ranges" is given, it MUST contain one slice object per dimension of the multi-dimensional array, representing slices for each dimension that cover the data given in the response.

- **Type**: List of Dictionaries.

- **Requirements/Conventions**:
    - **Support**: SHOULD be supported by all implementations, SHOULD NOT be `null`.

- **Examples**:
    - `""returned_ranges": [{"start": 10, "stop": 20, "step": 2}]"`
    - `""returned_ranges": [{"start": 10, "stop": 20, "step": 2}, {"start": 0, "stop": 9, "step": 1}]"`""",
        support=SupportLevel.SHOULD,
    )
    property_name: Optional[str] = OptimadeField(
        None,
        description="""The name of the property being provided.

- **Type**: string.

- **Requirements/Conventions**:
    - **Support**: OPTIONAL support in implementations, i.e., MAY be `null`..

- **Examples**:
    - `"cartesian_site_positions"`""",
        support=SupportLevel.OPTIONAL,
    )
    entry: Optional[dict] = OptimadeField(
        None,
        description=""" Object. An object that MUST have the following two keys:

    "id": String. The id of the entry of the property being provided.
    "type": String. The type of the entry of the property being provided.


- **Type**: string.

- **Requirements/Conventions**:
    - **Support**: OPTIONAL support in implementations, i.e., MAY be `null`..

- **Examples**:
    - `"{"id": "mpf_72", "type": structure"}`""",
        support=SupportLevel.OPTIONAL,
    )
    has_references: Optional[bool] = OptimadeField(
        None,
        description=""" An optional boolean to indicate whether any of the data lines in the response contains a reference marker. A value of false means that the client does not have to process any of the lines to detect reference markers, which may speed up the parsing.

- **Type**: boolean.

- **Requirements/Conventions**:
    - **Support**: OPTIONAL support in implementations, i.e., MAY be `null`..

- **Examples**:
    - `false`""",
        support=SupportLevel.OPTIONAL,
    )
    item_schema: Optional[dict] = OptimadeField(
        None,
        description="""An object that represents a JSON Schema that validates the data lines of the response. The format SHOULD be the relevant partial extract of a valid property definition as described in Property Definitions. If a schema is provided, it MUST be a valid JSON schema using the same version of JSON schema as described in that section.
- **Type**: dictionary.

- **Requirements/Conventions**:
    - **Support**: OPTIONAL support in implementations, i.e., MAY be `null`..
""",
        support=SupportLevel.OPTIONAL,
    )

    links: Optional[LinksObject] = OptimadeField(
        None,
        description=""" An object to provide relevant links for the property being provided. It MAY contain the following key:

    "base_url": String. The base URL of the implementation serving the database to which this property belongs.
    "item_describedby": String. A URL to an external JSON Schema that validates the data lines of the response. The format and requirements on this schema are the same as for the inline schema field item_schema.

- **Type**: dictionary.

- **Requirements/Conventions**:
    - **Support**: OPTIONAL support in implementations, i.e., MAY be `null`..
""",
        support=SupportLevel.OPTIONAL,
    )
    parent_id: Optional[dict] = OptimadeField(
        None,
        description="""The id of the entry to which this partial data belongs.
""",
        support=SupportLevel.OPTIONAL,
    )


class PartialDataFormat(BaseModel):
    header: PartialDataHeader
    data: list


class PartialDataResource(EntryResource):
    type: str = StrictField(
        "partial_data",
        description="""The name of the type of an entry.
        - **Type**: string.

        - **Requirements/Conventions**:
            - **Support**: MUST be supported by all implementations, MUST NOT be `null`.
            - **Query**: MUST be a queryable property with support for all mandatory filter features.
            - **Response**: REQUIRED in the response.
            - MUST be an existing entry type.
            - The entry of type `<type>` and ID `<id>` MUST be returned in response to a request for `/<type>/<id>` under the versioned base URL.

        - **Examples**:
            - `"structures"`""",
        regex="^structures$",
        support=SupportLevel.MUST,
        queryable=SupportLevel.MUST,
    )

    attributes: PartialDataHeader  # Todo make a better model for json response
