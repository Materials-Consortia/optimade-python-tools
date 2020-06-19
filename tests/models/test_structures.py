# pylint: disable=no-member
import pytest

from pydantic import ValidationError

from optimade.models.structures import StructureResource
from optimade.server.mappers import StructureMapper


def test_good_structures():
    """Check well-formed structures used as example data"""
    import optimade.server.data

    good_structures = optimade.server.data.structures

    for structure in good_structures:
        StructureResource(**StructureMapper.map_back(structure))


def test_more_good_structures(good_structures):
    """Check well-formed structures with specific edge-cases"""
    for index, structure in enumerate(good_structures):
        try:
            StructureResource(**StructureMapper.map_back(structure))
        except ValidationError:
            print(
                f"Good test structure {index} failed to validate from 'test_more_structures.json'"
            )
            raise


def test_bad_structures(bad_structures):
    """Check badly formed structures"""
    for index, structure in enumerate(bad_structures):
        print(f"Trying structure number {index} from 'test_bad_structures.json'")
        with pytest.raises(ValidationError):
            StructureResource(**StructureMapper.map_back(structure))
