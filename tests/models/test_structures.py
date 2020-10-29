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
    {"chemical_formula_anonymous": "AaBC"},
    {"chemical_formula_anonymous": "BC"},
    {"chemical_formula_anonymous": "A1B1"},
    {"chemical_formula_anonymous": "BC1"},
    {"chemical_formula_anonymous": "A9C"},
    {"chemical_formula_anonymous": "A9.2B"},
    {"chemical_formula_anonymous": "A2B90"},
    {"chemical_formula_anonymous": "A2B10"},
    {"chemical_formula_hill": "SiGe"},
    {"chemical_formula_hill": "GeHSi"},
    {"chemical_formula_hill": "CGeHSi"},
    {"chemical_formula_reduced": "Ge1.0Si1.0"},
    {"chemical_formula_reduced": "GeSi2.0"},
    {"chemical_formula_reduced": "GeSi.2"},
    {"chemical_formula_reduced": "Ge1Si"},
    {"chemical_formula_reduced": "GeSi1"},
    {"chemical_formula_reduced": "SiGe2"},
    {"chemical_formula_reduced": "FaKeElEmENtS"},
    {"chemical_formula_reduced": "abcd"},
    {"chemical_formula_reduced": "a2BeH"},
    {"chemical_formula_reduced": "............"},
    {"chemical_formula_reduced": "Ag6 Cl2"},
)


@pytest.mark.parametrize("deformity", deformities)
def test_structure_deformities(good_structure, deformity):
    """Make specific checks upon performing single invalidating deformations
    of the data of a good structure.

    """
    if deformity is None:
        StructureResource(**good_structure)
    else:
        good_structure["attributes"].update(deformity)
        with pytest.raises(ValidationError, match=fr".*{list(deformity.keys())[0]}.*"):
            StructureResource(**good_structure)
