""" This submodule defines constant values and definitions
from the OPTIMADE specification for use by the validator.

The `VALIDATOR_CONFIG` object can be imported and modified
before calling the validator inside a Python script to customise
the hardcoded values.

"""

from typing import Dict, Any, Set, NamedTuple
from pydantic import BaseSettings, Field

from optimade.models import InfoResponse, IndexInfoResponse, DataType, SupportLevel
from optimade.validator.utils import (
    ValidatorLinksResponse,
    ValidatorReferenceResponseOne,
    ValidatorReferenceResponseMany,
    ValidatorStructureResponseOne,
    ValidatorStructureResponseMany,
)

__all__ = ("ValidatorConfig", "VALIDATOR_CONFIG")


class FieldInfo(NamedTuple):
    support: SupportLevel
    queryable: SupportLevel
    type: DataType


_NON_ENTRY_ENDPOINTS = ("info", "links", "versions")


_RESPONSE_CLASSES = {
    "references": ValidatorReferenceResponseMany,
    "references/": ValidatorReferenceResponseOne,
    "structures": ValidatorStructureResponseMany,
    "structures/": ValidatorStructureResponseOne,
    "info": InfoResponse,
    "links": ValidatorLinksResponse,
}

_RESPONSE_CLASSES_INDEX = {
    "info": IndexInfoResponse,
    "links": ValidatorLinksResponse,
}

# This dictionary will eventually be set by getting the fields from response_classes directly
_FIELD_INFO = {
    "structures": {
        "id": FieldInfo(
            support=SupportLevel.MUST, queryable=SupportLevel.MUST, type=DataType.STRING
        ),
        "type": FieldInfo(
            support=SupportLevel.MUST, queryable=SupportLevel.MUST, type=DataType.STRING
        ),
        "structure_features": FieldInfo(
            support=SupportLevel.MUST, queryable=SupportLevel.MUST, type=DataType.LIST
        ),
        "last_modified": FieldInfo(
            support=SupportLevel.SHOULD,
            queryable=SupportLevel.MUST,
            type=DataType.TIMESTAMP,
        ),
        "elements": FieldInfo(
            support=SupportLevel.SHOULD, queryable=SupportLevel.MUST, type=DataType.LIST
        ),
        "nelements": FieldInfo(
            support=SupportLevel.SHOULD,
            queryable=SupportLevel.MUST,
            type=DataType.INTEGER,
        ),
        "elements_ratios": FieldInfo(
            support=SupportLevel.SHOULD, queryable=SupportLevel.MUST, type=DataType.LIST
        ),
        "chemical_formula_descriptive": FieldInfo(
            support=SupportLevel.SHOULD,
            queryable=SupportLevel.MUST,
            type=DataType.STRING,
        ),
        "chemical_formula_reduced": FieldInfo(
            support=SupportLevel.SHOULD,
            queryable=SupportLevel.MUST,
            type=DataType.STRING,
        ),
        "chemical_formula_anonymous": FieldInfo(
            support=SupportLevel.SHOULD,
            queryable=SupportLevel.MUST,
            type=DataType.STRING,
        ),
        "dimension_types": FieldInfo(
            support=SupportLevel.SHOULD,
            queryable=SupportLevel.OPTIONAL,
            type=DataType.LIST,
        ),
        "nperiodic_dimensions": FieldInfo(
            support=SupportLevel.SHOULD,
            queryable=SupportLevel.MUST,
            type=DataType.INTEGER,
        ),
        "lattice_vectors": FieldInfo(
            support=SupportLevel.SHOULD,
            queryable=SupportLevel.OPTIONAL,
            type=DataType.LIST,
        ),
        "cartesian_site_positions": FieldInfo(
            support=SupportLevel.SHOULD,
            queryable=SupportLevel.OPTIONAL,
            type=DataType.LIST,
        ),
        "nsites": FieldInfo(
            support=SupportLevel.SHOULD,
            queryable=SupportLevel.OPTIONAL,
            type=DataType.LIST,
        ),
        "species_at_sites": FieldInfo(
            support=SupportLevel.SHOULD,
            queryable=SupportLevel.OPTIONAL,
            type=DataType.LIST,
        ),
        "species": FieldInfo(
            support=SupportLevel.SHOULD,
            queryable=SupportLevel.OPTIONAL,
            type=DataType.LIST,
        ),
        "immutable_id": FieldInfo(
            support=SupportLevel.OPTIONAL,
            queryable=SupportLevel.MUST,
            type=DataType.STRING,
        ),
        "chemical_formula_hill": FieldInfo(
            support=SupportLevel.OPTIONAL,
            queryable=SupportLevel.OPTIONAL,
            type=DataType.STRING,
        ),
        "assemblies": FieldInfo(
            support=SupportLevel.OPTIONAL,
            queryable=SupportLevel.OPTIONAL,
            type=DataType.LIST,
        ),
    },
    "references": {
        "id": FieldInfo(
            support=SupportLevel.MUST, queryable=SupportLevel.MUST, type=DataType.STRING
        ),
        "type": FieldInfo(
            support=SupportLevel.MUST, queryable=SupportLevel.MUST, type=DataType.STRING
        ),
        "last_modified": FieldInfo(
            support=SupportLevel.SHOULD,
            queryable=SupportLevel.MUST,
            type=DataType.TIMESTAMP,
        ),
        "immutable_id": FieldInfo(
            support=SupportLevel.OPTIONAL,
            queryable=SupportLevel.OPTIONAL,
            type=DataType.STRING,
        ),
        "address": FieldInfo(
            support=SupportLevel.OPTIONAL,
            queryable=SupportLevel.OPTIONAL,
            type=DataType.STRING,
        ),
        "annote": FieldInfo(
            support=SupportLevel.OPTIONAL,
            queryable=SupportLevel.OPTIONAL,
            type=DataType.STRING,
        ),
        "booktitle": FieldInfo(
            support=SupportLevel.OPTIONAL,
            queryable=SupportLevel.OPTIONAL,
            type=DataType.STRING,
        ),
        "chapter": FieldInfo(
            support=SupportLevel.OPTIONAL,
            queryable=SupportLevel.OPTIONAL,
            type=DataType.STRING,
        ),
        "crossref": FieldInfo(
            support=SupportLevel.OPTIONAL,
            queryable=SupportLevel.OPTIONAL,
            type=DataType.STRING,
        ),
        "edition": FieldInfo(
            support=SupportLevel.OPTIONAL,
            queryable=SupportLevel.OPTIONAL,
            type=DataType.STRING,
        ),
        "howpublished": FieldInfo(
            support=SupportLevel.OPTIONAL,
            queryable=SupportLevel.OPTIONAL,
            type=DataType.STRING,
        ),
        "institution": FieldInfo(
            support=SupportLevel.OPTIONAL,
            queryable=SupportLevel.OPTIONAL,
            type=DataType.STRING,
        ),
        "journal": FieldInfo(
            support=SupportLevel.OPTIONAL,
            queryable=SupportLevel.OPTIONAL,
            type=DataType.STRING,
        ),
        "key": FieldInfo(
            support=SupportLevel.OPTIONAL,
            queryable=SupportLevel.OPTIONAL,
            type=DataType.STRING,
        ),
        "month": FieldInfo(
            support=SupportLevel.OPTIONAL,
            queryable=SupportLevel.OPTIONAL,
            type=DataType.STRING,
        ),
        "note": FieldInfo(
            support=SupportLevel.OPTIONAL,
            queryable=SupportLevel.OPTIONAL,
            type=DataType.STRING,
        ),
        "number": FieldInfo(
            support=SupportLevel.OPTIONAL,
            queryable=SupportLevel.OPTIONAL,
            type=DataType.STRING,
        ),
        "organization": FieldInfo(
            support=SupportLevel.OPTIONAL,
            queryable=SupportLevel.OPTIONAL,
            type=DataType.STRING,
        ),
        "pages": FieldInfo(
            support=SupportLevel.OPTIONAL,
            queryable=SupportLevel.OPTIONAL,
            type=DataType.STRING,
        ),
        "publisher": FieldInfo(
            support=SupportLevel.OPTIONAL,
            queryable=SupportLevel.OPTIONAL,
            type=DataType.STRING,
        ),
        "school": FieldInfo(
            support=SupportLevel.OPTIONAL,
            queryable=SupportLevel.OPTIONAL,
            type=DataType.STRING,
        ),
        "series": FieldInfo(
            support=SupportLevel.OPTIONAL,
            queryable=SupportLevel.OPTIONAL,
            type=DataType.STRING,
        ),
        "title": FieldInfo(
            support=SupportLevel.OPTIONAL,
            queryable=SupportLevel.OPTIONAL,
            type=DataType.STRING,
        ),
        "volume": FieldInfo(
            support=SupportLevel.OPTIONAL,
            queryable=SupportLevel.OPTIONAL,
            type=DataType.STRING,
        ),
        "year": FieldInfo(
            support=SupportLevel.OPTIONAL,
            queryable=SupportLevel.OPTIONAL,
            type=DataType.STRING,
        ),
        "bib_type": FieldInfo(
            support=SupportLevel.OPTIONAL,
            queryable=SupportLevel.OPTIONAL,
            type=DataType.STRING,
        ),
        "authors": FieldInfo(
            support=SupportLevel.OPTIONAL,
            queryable=SupportLevel.OPTIONAL,
            type=DataType.LIST,
        ),
        "editors": FieldInfo(
            support=SupportLevel.OPTIONAL,
            queryable=SupportLevel.OPTIONAL,
            type=DataType.LIST,
        ),
        "doi": FieldInfo(
            support=SupportLevel.OPTIONAL,
            queryable=SupportLevel.OPTIONAL,
            type=DataType.STRING,
        ),
        "url": FieldInfo(
            support=SupportLevel.OPTIONAL,
            queryable=SupportLevel.OPTIONAL,
            type=DataType.STRING,
        ),
    },
}

_UNIQUE_PROPERTIES = ("id", "immutable_id")

_INCLUSIVE_OPERATORS = {
    DataType.STRING: (
        "=",
        "<=",
        ">=",
        "CONTAINS",
        "STARTS WITH",
        "STARTS",
        "ENDS WITH",
        "ENDS",
    ),
    DataType.TIMESTAMP: (
        "=",
        "<=",
        ">=",
        "CONTAINS",
        "STARTS WITH",
        "STARTS",
        "ENDS WITH",
        "ENDS",
    ),
    DataType.INTEGER: (
        "=",
        "<=",
        ">=",
    ),
    DataType.FLOAT: (
        "=",
        "<=",
        ">=",
    ),
    DataType.LIST: ("HAS", "HAS ALL", "HAS ANY"),
}

exclusive_ops = ("!=", "<", ">")

_EXCLUSIVE_OPERATORS = {
    DataType.STRING: exclusive_ops,
    DataType.TIMESTAMP: exclusive_ops,
    DataType.FLOAT: exclusive_ops,
    DataType.INTEGER: exclusive_ops,
    DataType.LIST: (),
}


class ValidatorConfig(BaseSettings):
    """This class stores validator config parameters in a way that
    can be easily modified for testing niche implementations. Many
    of these fields are determined by the specification directly,
    but it may be desirable to modify them in certain cases.

    """

    response_classes: Dict[str, Any] = Field(
        _RESPONSE_CLASSES,
        description="Dictionary containing the mapping between endpoints and response classes for the main database",
    )

    response_classes_index: Dict[str, Any] = Field(
        _RESPONSE_CLASSES_INDEX,
        description="Dictionary containing the mapping between endpoints and response classes for the index meta-database",
    )

    field_info: Dict[str, Dict[str, FieldInfo]] = Field(
        _FIELD_INFO,
        description=(
            "Nested dictionary of endpoints -> field names -> FieldInfo containing support level, queryability and type. "
            "This field will be deprecated once the machinery to read the support levels of fields from their models directly is implemented."
        ),
    )

    unique_properties: Set[str] = Field(
        _UNIQUE_PROPERTIES,
        description=(
            "Fields that should be treated as unique indexes for all endpoints, "
            "i.e. fields on which filters should return at most one entry."
        ),
    )

    inclusive_operators: Dict[DataType, Set[str]] = Field(
        _INCLUSIVE_OPERATORS,
        description=(
            "Dictionary mapping OPTIMADE `DataType`s to a list of operators that are 'inclusive', "
            "i.e. those that should return entries with the matching value from the filter."
        ),
    )

    exclusive_operators: Dict[DataType, Set[str]] = Field(
        _EXCLUSIVE_OPERATORS,
        description=(
            "Dictionary mapping OPTIMADE `DataType`s to a list of operators that are 'exclusive', "
            "i.e. those that should not return entries with the matching value from the filter."
        ),
    )

    links_endpoint: str = Field("links", description="The name of the links endpoint")
    versions_endpoint: str = Field(
        "versions", description="The name of the versions endpoint"
    )

    info_endpoint: str = Field("info", description="The name of the info endpoint")
    non_entry_endpoints: Set[str] = Field(
        _NON_ENTRY_ENDPOINTS,
        description="The list specification-mandated endpoint names that do not contain entries",
    )


VALIDATOR_CONFIG = ValidatorConfig()
