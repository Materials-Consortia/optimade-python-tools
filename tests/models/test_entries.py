import pytest
from pydantic import ValidationError

from optimade.models.entries import EntryRelationships, EntryResource


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


def test_meta():
    good_entry_resource = {
        "id": "goodstruct123",
        "type": "structure",
        "attributes": {
            "last_modified": "2023-07-21T05:13:37.331Z",
            "elements": ["Ac"],
            "_exmpl_database_specific_property": "value1",
            "elements_ratios": [1.0],
        },
        "meta": {
            "property_metadata": {
                "elements_ratios": {
                    "_exmpl_mearsurement_method": "ICP-OES",
                },
                "_exmpl_database_specific_property": {
                    "_exmpl_metadata_property": "metadata_value"
                },
            }
        },
    }

    EntryResource(**good_entry_resource)

    # Test that other prefixed fields are allowed in meta
    good_entry_resource["meta"]["_other_database_specific_property"] = {
        "_exmpl_metadata_property": "entry 3"
    }

    EntryResource(**good_entry_resource)

    bad_entry_resources = [good_entry_resource.copy() for _ in range(4)]
    bad_entry_resources[0]["meta"]["property_metadata"][
        "_exmpl_database_specific_property"
    ] = {"metadata_property": "entry 0"}
    bad_entry_resources[1]["meta"]["property_metadata"][
        "database_specific_property"
    ] = {"_exmpl_metadata_property": "entry 1"}
    bad_entry_resources[2]["meta"]["database_specific_property"] = {
        "_exmpl_metadata_property": "entry 2"
    }

    for bad_entry in bad_entry_resources:
        with pytest.raises(ValueError):
            EntryResource(**bad_entry)
