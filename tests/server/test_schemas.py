"""Tests for optimade.server.schemas"""


def test_retrieve_queryable_properties() -> None:
    """Test that the default `ENTRY_INFO_SCHEMAS` contain
    all the required information about the OPTIMADE properties
    after dereferencing.

    """
    from optimade.models.entries import EntryResourceAttributes
    from optimade.server.schemas import (
        ENTRY_INFO_SCHEMAS,
        retrieve_queryable_properties,
    )

    for entry in ("Structures", "References"):
        schema = ENTRY_INFO_SCHEMAS[entry.lower()]

        top_level_props = ("id", "type", "attributes")
        properties = retrieve_queryable_properties(schema, top_level_props)

        attributes_annotation = schema.model_fields["attributes"].annotation
        assert issubclass(attributes_annotation, EntryResourceAttributes)
        fields = list(attributes_annotation.model_fields)
        fields += ["id", "type"]

        # Check all fields are present
        assert all(field in properties for field in fields)

        # Check that all expected keys are present for OPTIMADE fields
        for key in ("type", "sortable", "queryable", "description"):
            assert all(key in properties[field] for field in properties)

        # Check that all fields are queryable
        assert all(properties[field]["queryable"] for field in properties)


def test_provider_field_schemas() -> None:
    """Tests that the default configured provider fields that have descriptions
    are dereferenced appropriately.

    """
    from optimade.server.schemas import (
        ENTRY_INFO_SCHEMAS,
        retrieve_queryable_properties,
    )

    entry = "structures"
    test_field = "chemsys"
    schema = ENTRY_INFO_SCHEMAS[entry]
    top_level_props = ("id", "type", "attributes")
    properties = retrieve_queryable_properties(schema, top_level_props, entry)
    name = f"_exmpl_{test_field}"

    assert name in properties
    assert properties[name] == {
        "type": "string",
        "description": "A string representing the chemical system in an ordered fashion",
        "sortable": True,
    }
