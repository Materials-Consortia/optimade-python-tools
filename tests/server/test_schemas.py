from optimade.server.schemas import ENTRY_INFO_SCHEMAS, retrieve_queryable_properties


def test_schemas():
    """Test that the default `ENTRY_INFO_SCHEMAS` contain
    all the required information about the OPTIMADE properties
    after dereferencing.

    """
    for entry in ("Structures", "References"):
        schema = ENTRY_INFO_SCHEMAS[entry.lower()]()

        top_level_props = ("id", "type", "attributes")
        properties = retrieve_queryable_properties(schema, top_level_props)

        fields = list(
            schema["definitions"][f"{entry[:-1]}ResourceAttributes"][
                "properties"
            ].keys()
        )
        fields += ["id", "type"]

        # Check all fields are present
        assert all(field in properties for field in fields)

        # Check that there are no references to definitions remaining
        assert "$ref" not in properties
        assert not any("$ref" in properties[field] for field in properties)

        # Check that all expected keys are present for OPTIMADE fields
        for key in ("type", "sortable", "queryable", "description"):
            assert all(key in properties[field] for field in properties)


def test_provider_field_schemas():
    """Tests that the default configured provider fields that have descriptions
    are dereferenced appropriately.

    """
    entry = "structures"
    test_field = "chemsys"
    schema = ENTRY_INFO_SCHEMAS[entry]()
    top_level_props = ("id", "type", "attributes")
    properties = retrieve_queryable_properties(schema, top_level_props, entry)
    name = f"_exmpl_{test_field}"

    assert name in properties
    assert properties[name] == {
        "type": "string",
        "description": "A string representing the chemical system in an ordered fashion",
        "sortable": True,
    }
