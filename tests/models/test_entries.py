import pytest
from pydantic import ValidationError

from optimade.models.entries import EntryRelationships


def test_simple_relationships():
    """Make sure relationship resources are added to the correct relationship"""

    good_relationships = (
        {"references": {"data": [{"id": "dijkstra1968", "type": "references"}]}},
        {"structures": {"data": [{"id": "dijkstra1968", "type": "structures"}]}},
    )
    for relationship in good_relationships:
        EntryRelationships(**relationship)

    bad_relationships = (
        {"references": {"data": [{"id": "dijkstra1968", "type": "structures"}]}},
        {"structures": {"data": [{"id": "dijkstra1968", "type": "references"}]}},
    )
    for relationship in bad_relationships:
        with pytest.raises(ValidationError):
            EntryRelationships(**relationship)


def test_advanced_relationships():
    """Make sure the rules for the base resource 'meta' field are upheld"""

    relationship = {
        "references": {
            "data": [
                {
                    "id": "dijkstra1968",
                    "type": "references",
                    "meta": {
                        "description": "Reference for the search algorithm Dijkstra."
                    },
                }
            ]
        }
    }
    EntryRelationships(**relationship)

    relationship = {
        "references": {
            "data": [{"id": "dijkstra1968", "type": "references", "meta": {}}]
        }
    }
    with pytest.raises(ValidationError):
        EntryRelationships(**relationship)
