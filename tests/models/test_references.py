# pylint: disable=no-member
import pytest

from optimade.models.references import ReferenceResource


MAPPER = "ReferenceMapper"


def test_good_references(mapper):
    """Check well-formed references used as example data"""
    import optimade.server.data

    good_refs = optimade.server.data.references
    for doc in good_refs:
        ReferenceResource(**mapper(MAPPER).map_back(doc))


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
