# pylint: disable=no-member
import pytest

from pydantic import ValidationError

from optimade.models.structures import StructureResource


MAPPER = "StructureMapper"


def test_good_structures(mapper):
    """Check well-formed structures used as example data"""
    import optimade.server.data

    good_structures = optimade.server.data.structures

    for structure in good_structures:
        StructureResource(**mapper(MAPPER).map_back(structure))


def test_more_good_structures(good_structures, mapper):
    """Check well-formed structures with specific edge-cases"""
    for index, structure in enumerate(good_structures):
        try:
            StructureResource(**mapper(MAPPER).map_back(structure))
        except ValidationError:
            # Printing to keep the original exception as is, while still being informational
            print(
                f"Good test structure {index} failed to validate from 'test_more_structures.json'"
            )
            raise


def test_bad_structures(bad_structures, mapper):
    """Check badly formed structures"""
    for index, structure in enumerate(bad_structures):
        # This is for helping devs finding any errors that may occur
        print(f"Trying structure number {index} from 'test_bad_structures.json'")
        with pytest.raises(ValidationError):
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
        "'chemical_formula_anonymous' A1B1 must omit proportion '1'",
    ),
    (
        {"chemical_formula_anonymous": "BC1"},
        "'chemical_formula_anonymous' BC1 must omit proportion '1'",
    ),
    (
        {"chemical_formula_anonymous": "A9C"},
        "'chemical_formula_anonymous' A9C has wrong labels: ('A', 'C') vs expected ('A', 'B')",
    ),
    (
        {"chemical_formula_anonymous": "A9.2B"},
        "chemical_formula_anonymous\n  string does not match regex",
    ),
    (
        {"chemical_formula_anonymous": "A2B90"},
        "'chemical_formula_anonymous' A2B90 has wrong order: elements with highest proportion should appear first: [2, 90] vs expected [90, 2]",
    ),
    (
        {"chemical_formula_anonymous": "A2B10"},
        "'chemical_formula_anonymous' A2B10 has wrong order: elements with highest proportion should appear first: [2, 10] vs expected [10, 2]",
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
        "chemical_formula_reduced\n  string does not match regex",
    ),
    (
        {"chemical_formula_reduced": "GeSi2.0"},
        "chemical_formula_reduced\n  string does not match regex",
    ),
    (
        {"chemical_formula_reduced": "GeSi.2"},
        "chemical_formula_reduced\n  string does not match regex",
    ),
    (
        {"chemical_formula_reduced": "Ge1Si"},
        "Must omit proportion '1' from formula Ge1Si in 'chemical_formula_reduced'",
    ),
    (
        {"chemical_formula_reduced": "GeSi1"},
        "Must omit proportion '1' from formula GeSi1 in 'chemical_formula_reduced'",
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
        "chemical_formula_reduced\n  string does not match regex",
    ),
    (
        {"chemical_formula_reduced": "a2BeH"},
        "chemical_formula_reduced\n  string does not match regex",
    ),
    (
        {"chemical_formula_reduced": "............"},
        "chemical_formula_reduced\n  string does not match regex",
    ),
    (
        {"chemical_formula_reduced": "Ag6 Cl2"},
        "chemical_formula_reduced\n  string does not match regex",
    ),
)


@pytest.mark.parametrize("deformity", deformities)
def test_structure_deformities(good_structure, deformity):
    """Make specific checks upon performing single invalidating deformations
    of the data of a good structure.

    """
    import re

    if deformity is None:
        return StructureResource(**good_structure)

    deformity, message = deformity
    good_structure["attributes"].update(deformity)
    with pytest.raises(ValidationError, match=fr".*{re.escape(message)}.*"):
        StructureResource(**good_structure)
