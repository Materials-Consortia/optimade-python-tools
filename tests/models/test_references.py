# pylint: disable=no-member
import pytest
from pydantic import ValidationError

from optimade.models.references import ReferenceResource

MAPPER = "ReferenceMapper"


def test_more_good_references(good_references, mapper):
    """Check well-formed structures with specific edge-cases"""
    for index, structure in enumerate(good_references):
        try:
            ReferenceResource(**mapper(MAPPER).map_back(structure))
        except ValidationError:
            # Printing to keep the original exception as is, while still being informational
            print(
                f"Good test structure {index} failed to validate from 'test_good_structures.json'"
            )
            raise


def test_bad_references(mapper):
    """Check badly formed references"""
    from pydantic import ValidationError

    bad_refs = [
        {"id": "AAAA", "type": "references", "doi": "10.1234/1234"},  # bad id
        {"id": "newton1687", "type": "references"},  # missing all fields
        {"id": "newton1687", "type": "reference", "doi": "10.1234/1234"},  # wrong type
    ]

    for ref in bad_refs:
        with pytest.raises(ValidationError):
            ReferenceResource(**mapper(MAPPER).map_back(ref))
