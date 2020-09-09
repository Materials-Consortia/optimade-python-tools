""" This submodule defines constant values and definitions
from the OPTIMADE specification for use by the validator.

The `VALIDATOR_CONFIG` object can be imported and modified
before calling the valiator inside a Python script to customise
the hardcoded values.

"""

from typing import Dict, Any, Set
from pydantic import BaseSettings, Field

from optimade.models import InfoResponse, IndexInfoResponse, DataType
from optimade.validator.utils import (
    ValidatorLinksResponse,
    ValidatorReferenceResponseOne,
    ValidatorReferenceResponseMany,
    ValidatorStructureResponseOne,
    ValidatorStructureResponseMany,
)

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
_PROPERTIES = {
    "structures": {
        "MUST": (
            "id",
            "type",
            "structure_features",
        ),
        "SHOULD": (
            "last_modified",
            "elements",
            "nelements",
            "elements_ratios",
            "chemical_formula_descriptive",
            "chemical_formula_reduced",
            "chemical_formula_anonymous",
            "dimension_types",
            "nperiodic_dimensions",
            "lattice_vectors",
            "cartesian_site_positions",
            "nsites",
            "species_at_sites",
            "species",
        ),
        "OPTIONAL": (
            "immutable_id",
            "chemical_formula_hill",
            "assemblies",
        ),
    },
    "references": {
        "MUST": ("id", "type"),
        "SHOULD": (),
        "OPTIONAL": (
            "last_modified",
            "immutable_id",
            "address",
            "annote",
            "booktitle",
            "chapter",
            "crossref",
            "edition",
            "howpublished",
            "institution",
            "journal",
            "key",
            "month",
            "note",
            "number",
            "organization",
            "pages",
            "publisher",
            "school",
            "series",
            "title",
            "volume",
            "year",
            "bib_type",
            "authors",
            "editors",
            "doi",
            "url",
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

    entry_properties: Dict[str, Dict[str, Set[str]]] = Field(
        _PROPERTIES,
        description=(
            "Nested dictionary of endpoints -> support level -> list of field names. "
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
