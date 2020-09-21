from optimade.server.schemas import ENTRY_INFO_SCHEMAS, retrieve_queryable_properties


def test_schemas():

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

        assert all(field in properties for field in fields)
