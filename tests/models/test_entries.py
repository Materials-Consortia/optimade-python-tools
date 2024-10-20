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
    import copy

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

    bad_entry_resources = [
        good_entry_resource,
        copy.deepcopy(good_entry_resource),
        copy.deepcopy(good_entry_resource),
        copy.deepcopy(good_entry_resource),
    ]
    bad_entry_resources[0]["meta"]["property_metadata"][
        "_exmpl_database_specific_property"
    ] = {"metadata_property": "metadata_value"}
    bad_entry_resources[1]["meta"]["property_metadata"][
        "database_specific_property"
    ] = {"_exmpl_metadata_property": "metadata_value"}
    bad_entry_resources[2]["meta"]["database_specific_property"] = {
        "_exmpl_metadata_property": "metadata_value"
    }
    bad_entry_resources[3]["meta"]["_other_database_specific_property"] = {
        "_exmpl_metadata_property": "metadata_value"
    }

    for bad_entry in bad_entry_resources:
        with pytest.raises(ValueError):
            EntryResource(**bad_entry)
