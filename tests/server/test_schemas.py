"""Tests for optimade.server.schemas"""

import pytest


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
    from optimade.server.config import ServerConfig
    from optimade.server.schemas import (
        ENTRY_INFO_SCHEMAS,
        retrieve_queryable_properties,
    )

    config = ServerConfig()

    entry = "structures"
    test_field = "chemsys"
    schema = ENTRY_INFO_SCHEMAS[entry]
    top_level_props = ("id", "type", "attributes")
    properties = retrieve_queryable_properties(schema, top_level_props, entry, config)
    name = f"_exmpl_{test_field}"

    assert name in properties
    assert properties[name] == {
        "type": "string",
        "description": "A string representing the chemical system in an ordered fashion",
        "sortable": True,
    }


FULL_DEFINITION = {
    "$id": "https://example.org/defs/v1.0/properties/exmpl/structures/_exmpl_cell_volume",
    "title": "cell volume",
    "description": "The volume of the cell per formula unit.",
    "x-optimade-type": "float",
    "x-optimade-unit": "angstrom^3",
    "x-optimade-unit-definitions": [
        {
            "symbol": "angstrom",
            "title": "ångström",
            "display-symbol": "Å",
            "description": "The ångström unit of length.",
            "standard": {"name": "gnu units", "symbol": "angstrom"},
        }
    ],
    "type": ["number", "null"],
    "x-optimade-implementation": {"query-support": "all mandatory"},
}


@pytest.mark.parametrize("entry_type", ["structures", "references", "files"])
def test_retrieve_property_definitions(entry_type) -> None:
    """Test that the default `ENTRY_INFO_SCHEMAS` are described by the
    standard property definitions."""
    from optimade.models import PropertyDefinition
    from optimade.server.schemas import (
        ENTRY_INFO_SCHEMAS,
        retrieve_property_definitions,
        retrieve_queryable_properties,
    )

    schema = ENTRY_INFO_SCHEMAS[entry_type]
    definitions = retrieve_property_definitions(schema, entry_type)

    # The same properties should be described in both formats
    assert set(definitions) == set(
        retrieve_queryable_properties(schema, ("id", "type", "attributes"))
    )

    for name, definition in definitions.items():
        PropertyDefinition.model_validate(definition)
        assert definition["$id"].startswith("https://schemas.optimade.org/defs/")
        assert definition["$schema"].startswith("https://schemas.optimade.org/meta/")
        assert definition["x-optimade-implementation"]["sortable"] is True
        assert (
            definition["x-optimade-implementation"]["query-support"]
            == definition["x-optimade-requirements"]["query-support"]
        )


def test_property_definitions_for_custom_models() -> None:
    """Test that fields that are not part of the specification are defined
    based on their pydantic model."""
    from typing import Annotated

    from optimade.models import (
        PropertyDefinition,
        StructureResource,
        StructureResourceAttributes,
    )
    from optimade.models.utils import OptimadeField, StrictField
    from optimade.server.schemas import retrieve_property_definitions

    class MyStructureResourceAttributes(StructureResourceAttributes):
        exmpl_tags: Annotated[
            list[str] | None, StrictField(description="Some tags.")
        ] = None
        exmpl_nsteps: Annotated[
            int | None,
            OptimadeField(description="The number of steps.", sortable=False),
        ] = None

    class MyStructureResource(StructureResource):
        attributes: MyStructureResourceAttributes

    definitions = retrieve_property_definitions(MyStructureResource, "structures")
    assert (
        definitions["nsites"]["$id"]
        == "https://schemas.optimade.org/defs/v1.2/properties/optimade/structures/nsites"
    )

    PropertyDefinition.model_validate(definitions["exmpl_tags"])
    assert definitions["exmpl_tags"]["x-optimade-type"] == "list"
    assert definitions["exmpl_tags"]["type"] == ["array", "null"]
    assert definitions["exmpl_tags"]["items"]["x-optimade-type"] == "string"
    assert definitions["exmpl_tags"]["x-optimade-implementation"] == {"sortable": True}

    assert definitions["exmpl_nsteps"]["x-optimade-type"] == "integer"
    assert definitions["exmpl_nsteps"]["x-optimade-implementation"] == {
        "sortable": False
    }

    # Entry types that are not part of the specification are defined in the same way
    definitions = retrieve_property_definitions(MyStructureResource, "exmpl_entries")
    assert definitions["nsites"]["$id"].startswith("urn:uuid:")
    assert definitions["nsites"]["x-optimade-type"] == "integer"


def test_provider_field_definitions() -> None:
    """Tests that provider fields can be configured with full property
    definitions, which are served alongside those created from simple descriptions."""
    from optimade.models import PropertyDefinition
    from optimade.server.config import ServerConfig
    from optimade.server.schemas import (
        ENTRY_INFO_SCHEMAS,
        retrieve_property_definitions,
        retrieve_queryable_properties,
    )

    config = ServerConfig(
        provider_fields={
            "structures": [
                "band_gap",
                {
                    "name": "cell_volume",
                    "sortable": False,
                    "definition": FULL_DEFINITION,
                },
                {
                    "definition": {
                        "description": "The number of steps.",
                        "x-optimade-definition": {"name": "_exmpl_nsteps"},
                        "x-optimade-type": "integer",
                        "x-optimade-unit": "dimensionless",
                        "type": ["integer", "null"],
                    }
                },
                {
                    "name": "energy",
                    "type": "float",
                    "unit": "eV",
                    "description": "The energy.",
                },
                {"name": "tags", "type": "list", "description": "Some tags."},
            ]
        }
    )

    schema = ENTRY_INFO_SCHEMAS["structures"]
    definitions = retrieve_property_definitions(schema, "structures", config)
    for definition in definitions.values():
        PropertyDefinition.model_validate(definition)

    # The provided definition should be passed through, with defaults for missing keys
    cell_volume = definitions["_exmpl_cell_volume"]
    for key in FULL_DEFINITION:
        if key != "x-optimade-implementation":
            assert cell_volume[key] == FULL_DEFINITION[key]
    assert cell_volume["$schema"] == (
        "https://schemas.optimade.org/meta/v1.2/optimade/property_definition.json"
    )
    assert cell_volume["x-optimade-definition"] == {
        "kind": "property",
        "format": "1.2",
        "name": "_exmpl_cell_volume",
        "label": "_exmpl_cell_volume_structures",
    }
    assert cell_volume["x-optimade-implementation"] == {
        "sortable": False,
        "query-support": "all mandatory",
    }

    # The name can also be taken from the definition itself
    assert definitions["_exmpl_nsteps"]["x-optimade-type"] == "integer"
    assert definitions["_exmpl_nsteps"]["$id"].startswith("urn:uuid:")

    # Simple descriptions are converted where possible
    assert definitions["_exmpl_energy"]["x-optimade-unit"] == "eV"
    assert definitions["_exmpl_energy"]["x-optimade-implementation"] == {
        "sortable": True
    }
    assert "_exmpl_tags" not in definitions
    assert "_exmpl_band_gap" not in definitions

    # Fully defined fields can still be served in the old format
    properties = retrieve_queryable_properties(
        schema, ("id", "type", "attributes"), "structures", config
    )
    assert properties["_exmpl_cell_volume"] == {
        "description": "The volume of the cell per formula unit.",
        "type": "float",
        "unit": "angstrom^3",
        "sortable": False,
    }
    assert properties["_exmpl_nsteps"] == {
        "description": "The number of steps.",
        "type": "integer",
        "sortable": True,
    }
    assert properties["_exmpl_tags"] == {
        "type": "list",
        "description": "Some tags.",
        "sortable": True,
    }


def test_bad_provider_field_definitions() -> None:
    """Tests that invalid definitions of provider fields are caught by the config."""
    from pydantic import ValidationError

    from optimade.server.config import ServerConfig

    for bad_field in (
        # No name
        {"description": "A field."},
        {"definition": {**FULL_DEFINITION}},
        # Bad definitions
        {"name": "cell_volume", "definition": "cell_volume.json"},
        {"name": "cell_volume", "definition": {"description": "The volume."}},
        {
            "name": "cell_volume",
            "definition": {**FULL_DEFINITION, "type": ["string", "null"]},
        },
    ):
        with pytest.raises(ValidationError):
            ServerConfig(provider_fields={"structures": [bad_field]})
