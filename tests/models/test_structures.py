import itertools
from typing import TYPE_CHECKING

import pytest

from optimade.models.structures import Periodicity, StructureFeatures
from optimade.warnings import MissingExpectedField

if TYPE_CHECKING:
    from collections.abc import Callable, Generator
    from typing import Any, Optional

    from optimade.server.mappers import BaseResourceMapper

MAPPER = "StructureMapper"


@pytest.mark.filterwarnings("ignore", category=MissingExpectedField)
def test_good_structure_with_missing_data(good_structure: "dict[str, Any]") -> None:
    """Check deserialization of well-formed structure used
    as example data with all combinations of null values
    in non-mandatory fields.
    """
    from optimade.models.structures import StructureResource

    structure = {field: good_structure[field] for field in good_structure}

    # Have to include `assemblies` here, although it is only optional,
    # `structure_features = ['assemblies']` in the test document so it
    # is effectively mandatory
    mandatory_fields = ("id", "type", "structure_features", "assemblies")

    total_fields = [
        field
        for field in structure["attributes"].keys()
        if field not in mandatory_fields
    ]
    for r in range(len(total_fields)):
        for f in itertools.combinations(total_fields, r=r):
            incomplete_structure = {field: structure[field] for field in structure}
            for field in f:
                incomplete_structure["attributes"][field] = None

            StructureResource(**incomplete_structure)


def test_more_good_structures(
    good_structures: "list[dict[str, Any]]",
    mapper: "Callable[[str], BaseResourceMapper]",
) -> None:
    """Check well-formed structures with specific edge-cases"""
    from pydantic import ValidationError

    from optimade.models.structures import StructureResource

    for index, structure in enumerate(good_structures):
        try:
            s = StructureResource(**mapper(MAPPER).map_back(structure))
            if s.attributes.structure_features:
                assert isinstance(s.attributes.structure_features[0], StructureFeatures)
            for dim in s.attributes.dimension_types:
                assert isinstance(dim, Periodicity)
        except ValidationError:
            # Printing to keep the original exception as is, while still being informational
            print(
                f"Good test structure {index} failed to validate from 'test_good_structures.json'"
            )
            raise


def test_bad_structures(
    bad_structures: "list[dict[str, Any]]",
    mapper: "Callable[[str], BaseResourceMapper]",
) -> None:
    """Check badly formed structures.

    NOTE: Only ValueError, AssertionError, and PydanticCustomError are wrapped in
    ValidationError exceptions. All other exceptions are "bubbled up" as is. See
    https://docs.pydantic.dev/latest/concepts/validators/#handling-errors-in-validators
    for more information.
    """
    from pydantic import ValidationError

    from optimade.models.structures import StructureResource

    with pytest.warns(MissingExpectedField):
        for index, structure in enumerate(bad_structures):
            # This is for helping devs finding any errors that may occur
            print(
                f"Trying structure number {index}/{len(bad_structures)} from 'test_bad_structures.json'"
            )
            with pytest.raises((ValidationError, TypeError)):
                StructureResource(**mapper(MAPPER).map_back(structure))


deformities = (
    None,
    (
        {"chemical_formula_anonymous": "AaBC"},
        "'chemical_formula_anonymous' AaBC has wrong labels: ('Aa', 'B', 'C') vs expected ('A', 'B', 'C')",
    ),
    (
        {"chemical_formula_anonymous": "BC"},
        "'chemical_formula_anonymous' BC has wrong labels: ('B', 'C') vs expected ('A', 'B')",
    ),
    (
        {"chemical_formula_anonymous": "A1B1"},
        "String should match pattern",
    ),
    (
        {"chemical_formula_anonymous": "BC1"},
        "String should match pattern",
    ),
    (
        {"chemical_formula_anonymous": "A9C"},
        "'chemical_formula_anonymous' A9C has wrong labels: ('A', 'C') vs expected ('A', 'B')",
    ),
    (
        {"chemical_formula_anonymous": "A9.2B"},
        "chemical_formula_anonymous\n  String should match pattern",
    ),
    (
        {"chemical_formula_anonymous": "A2B90"},
        "'chemical_formula_anonymous' A2B90 has wrong order: elements with highest proportion should appear first: [2, 90] vs expected [90, 2]",
    ),
    (
        {"chemical_formula_anonymous": "AB10"},
        "'chemical_formula_anonymous' AB10 has wrong order: elements with highest proportion should appear first: [1, 10] vs expected [10, 1]",
    ),
    (
        {"chemical_formula_hill": "SiGe"},
        "Elements in 'chemical_formula_hill' must appear in Hill order: ['Ge', 'Si'] not ['Si', 'Ge']",
    ),
    (
        {"chemical_formula_hill": "HGeSi"},
        "Elements in 'chemical_formula_hill' must appear in Hill order: ['Ge', 'H', 'Si'] not ['H', 'Ge', 'Si']",
    ),
    (
        {"chemical_formula_hill": "CGeHSi"},
        "Elements in 'chemical_formula_hill' must appear in Hill order: ['C', 'H', 'Ge', 'Si'] not ['C', 'Ge', 'H', 'Si']",
    ),
    (
        {"chemical_formula_hill": "HCGeSi"},
        "Elements in 'chemical_formula_hill' must appear in Hill order: ['C', 'H', 'Ge', 'Si'] not ['H', 'C', 'Ge', 'Si']",
    ),
    (
        {"chemical_formula_reduced": "Ge1.0Si1.0"},
        "chemical_formula_reduced\n  String should match pattern",
    ),
    (
        {"chemical_formula_reduced": "GeSi2.0"},
        "chemical_formula_reduced\n  String should match pattern",
    ),
    (
        {"chemical_formula_reduced": "GeSi.2"},
        "chemical_formula_reduced\n  String should match pattern",
    ),
    (
        {"chemical_formula_reduced": "Ge1Si"},
        "String should match pattern",
    ),
    (
        {"chemical_formula_reduced": "GeSi1"},
        "String should match pattern",
    ),
    (
        {"chemical_formula_reduced": "SiGe2"},
        "Elements in 'chemical_formula_reduced' must appear in alphabetical order: ['Ge', 'Si'] not ['Si', 'Ge']",
    ),
    (
        {"chemical_formula_reduced": "FaKeElEmENtS"},
        "Cannot use unknown chemical symbols ['Fa', 'Ke', 'El', 'Em', 'E', 'Nt'] in 'chemical_formula_reduced'",
    ),
    (
        {"chemical_formula_reduced": "abcd"},
        "chemical_formula_reduced\n  String should match pattern",
    ),
    (
        {"chemical_formula_reduced": "a2BeH"},
        "chemical_formula_reduced\n  String should match pattern",
    ),
    (
        {"chemical_formula_reduced": "............"},
        "chemical_formula_reduced\n  String should match pattern",
    ),
    (
        {"chemical_formula_reduced": "Ag6 Cl2"},
        "chemical_formula_reduced\n  String should match pattern",
    ),
    (
        {"chemical_formula_reduced": "Ge2Si2"},
        "chemical_formula_reduced 'Ge2Si2' is not properly reduced: expected 'GeSi'.",
    ),
    (
        {"chemical_formula_reduced": "Ge144Si60V24"},
        "chemical_formula_reduced 'Ge144Si60V24' is not properly reduced: expected 'Ge12Si5V2'.",
    ),
    (
        {"chemical_formula_anonymous": "A10B5C5"},
        "chemical_formula_anonymous 'A10B5C5' is not properly reduced: expected 'A2BC'",
    ),
    (
        {"chemical_formula_anonymous": "A44B15C9D4E3F2GHI0J0K0L0"},
        "String should match pattern",
    ),
)


@pytest.mark.parametrize("deformity", deformities)
def test_structure_fatal_deformities(
    good_structure: "dict[str, Any]", deformity: "Optional[tuple[dict[str, str], str]]"
) -> None:
    """Make specific checks upon performing single invalidating deformations
    of the data of a good structure.

    """
    import re

    from pydantic import ValidationError

    from optimade.models.structures import StructureResource

    if deformity is None:
        StructureResource(**good_structure)
        return

    deformity_change, message = deformity
    good_structure["attributes"].update(deformity_change)
    with pytest.raises(ValidationError, match=rf".*{re.escape(message)}.*"):
        StructureResource(**good_structure)


def _minor_deformities() -> "Generator[dict[str, Any], None, None]":
    """Generate minor deformities from correlated structure fields"""
    from optimade.models.structures import CORRELATED_STRUCTURE_FIELDS

    return ({f: None} for f in {f for _ in CORRELATED_STRUCTURE_FIELDS for f in _})


@pytest.mark.parametrize("deformity", _minor_deformities())
def test_structure_minor_deformities(
    good_structure: "dict[str, Any]", deformity: "Optional[dict[str, Any]]"
) -> None:
    """Make specific checks upon performing single minor invalidations
    of the data of a good structure that should emit warnings.
    """
    from optimade.models.structures import StructureResource

    if deformity is None:
        StructureResource(**good_structure)
    else:
        good_structure["attributes"].update(deformity)
        with pytest.warns(MissingExpectedField):
            StructureResource(**good_structure)
