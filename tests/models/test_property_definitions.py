"""Tests for the OPTIMADE Property Definition models and the bundled standard definitions."""

import copy
from typing import Annotated

import pytest
from pydantic import BaseModel, Field, TypeAdapter, ValidationError

from optimade.models import (
    FileResource,
    PropertyDefinition,
    ReferenceResource,
    StructureResource,
)
from optimade.models.property_definitions import (
    complete_property_definition,
    get_meta_schema_url,
    get_standard_entry_type_definition,
    property_definition_from_description,
    property_definition_from_json_schema,
)

ENTRY_RESOURCES = {
    "structures": StructureResource,
    "references": ReferenceResource,
    "files": FileResource,
}

DEFINITION = {
    "$id": "https://example.org/defs/v1.0/properties/exmpl/structures/_exmpl_forces",
    "$schema": "https://schemas.optimade.org/meta/v1.2/optimade/property_definition.json",
    "title": "forces",
    "description": "The forces on each site.",
    "x-optimade-definition": {
        "kind": "property",
        "format": "1.2",
        "name": "_exmpl_forces",
        "label": "_exmpl_forces_structures",
        "version": "1.0.0",
    },
    "x-optimade-type": "list",
    "x-optimade-unit": "inapplicable",
    "x-optimade-dimensions": {
        "names": ["dim_sites", "dim_spatial"],
        "sizes": [None, 3],
    },
    "x-optimade-unit-definitions": [
        {
            "symbol": "eV",
            "title": "electronvolt",
            "display-symbol": "eV",
            "description": "The electronvolt.",
            "standard": {"name": "gnu units", "symbol": "eV"},
        },
        {
            "symbol": "angstrom",
            "title": "ångström",
            "display-symbol": "Å",
            "description": "The ångström.",
            "standard": {"name": "gnu units", "symbol": "angstrom"},
        },
    ],
    "type": ["array", "null"],
    "items": {
        "x-optimade-type": "list",
        "x-optimade-unit": "inapplicable",
        "type": ["array"],
        "items": {
            "x-optimade-type": "float",
            "x-optimade-unit": "angstrom^-1*eV",
            "type": ["number"],
        },
    },
    "x-optimade-implementation": {"sortable": False, "query-support": "none"},
    "x-exmpl-internal-key": "forces",
}


def test_get_meta_schema_url():
    assert (
        get_meta_schema_url()
        == "https://schemas.optimade.org/meta/v1.2/optimade/property_definition.json"
    )
    assert (
        get_meta_schema_url("1.3")
        == "https://schemas.optimade.org/meta/v1.3/optimade/property_definition.json"
    )


@pytest.mark.parametrize("entry_type", ENTRY_RESOURCES)
def test_standard_definitions(entry_type):
    """Check that the bundled standard definitions are valid, are preserved when
    passed through the models, and describe the same properties as the pydantic
    models for each entry type."""
    entry_type_definition = get_standard_entry_type_definition(entry_type)
    assert entry_type_definition["x-optimade-definition"]["kind"] == "entrytype"
    assert entry_type_definition["x-optimade-definition"]["name"] == entry_type

    properties = entry_type_definition["properties"]
    for name, definition in properties.items():
        definition["$schema"] = get_meta_schema_url(
            definition["x-optimade-definition"]["format"]
        )
        validated = PropertyDefinition.model_validate(definition)
        assert validated.definition.name == name
        assert (
            validated.model_dump(by_alias=True, exclude_unset=True, mode="json")
            == definition
        )

    resource = ENTRY_RESOURCES[entry_type]
    attributes = resource.model_fields["attributes"].annotation
    assert set(properties) == set(attributes.model_fields) | {"id", "type"}

    # The bundled definitions should not be mutated by users
    assert "$schema" not in next(
        iter(get_standard_entry_type_definition(entry_type)["properties"].values())
    )

    assert get_standard_entry_type_definition("unknown") is None


def test_property_definition():
    validated = PropertyDefinition.model_validate(DEFINITION)
    assert validated.optimade_type == "list"
    assert validated.items.items.unit == "angstrom^-1*eV"
    assert validated.dimensions.sizes == [None, 3]
    assert validated.implementation.sortable is False
    assert validated.model_dump(by_alias=True, exclude_unset=True, mode="json") == (
        DEFINITION
    )


@pytest.mark.parametrize(
    "updates,removals",
    [
        # Missing keys that are mandatory at the outermost level
        ({}, ["$id"]),
        ({}, ["$schema"]),
        ({}, ["title"]),
        ({}, ["description"]),
        ({}, ["x-optimade-definition"]),
        # Missing keys that are mandatory at all levels
        ({}, ["x-optimade-type"]),
        ({}, ["x-optimade-unit"]),
        ({}, ["type"]),
        # Mismatched or badly formed types
        ({"type": ["object", "null"]}, []),
        ({"type": "array"}, []),
        ({"type": ["array", "string"]}, []),
        ({"x-optimade-type": "array"}, []),
        ({}, ["items"]),
        ({"x-optimade-type": "dictionary", "type": ["object"]}, []),
        # List lengths must be described by the dimensions
        ({"maxItems": 3}, []),
        ({"x-optimade-dimensions": {"names": ["dim_sites"], "sizes": [None, 3]}}, []),
        # Units must be defined
        ({}, ["x-optimade-unit-definitions"]),
        # Operators are only allowed for partial query support
        ({"x-optimade-implementation": {"query-support": "partial"}}, []),
        (
            {
                "x-optimade-implementation": {
                    "query-support": "none",
                    "query-support-operators": ["="],
                }
            },
            [],
        ),
        ({"x-optimade-implementation": {"query-support": "some"}}, []),
    ],
)
def test_bad_property_definitions(updates, removals):
    definition = copy.deepcopy(DEFINITION)
    definition.update(updates)
    for key in removals:
        definition.pop(key)

    with pytest.raises(ValidationError):
        PropertyDefinition.model_validate(definition)


def test_provider_specific_type():
    """Provider-specific data types can be carried by any JSON type."""
    definition = copy.deepcopy(DEFINITION)
    definition["x-optimade-type"] = "_exmpl_tensor"
    PropertyDefinition.model_validate(definition)

    definition["type"] = ["string"]
    definition.pop("items")
    PropertyDefinition.model_validate(definition)


def test_complete_property_definition():
    partial = {
        "description": "The band gap.",
        "x-optimade-type": "float",
        "x-optimade-unit": "dimensionless",
        "type": ["number", "null"],
    }
    definition = complete_property_definition(partial, "_exmpl_band_gap", "structures")
    assert "$id" not in partial, "The input should not be modified"
    assert definition["$schema"] == get_meta_schema_url()
    assert definition["title"] == "_exmpl_band_gap"
    assert definition["x-optimade-definition"] == {
        "kind": "property",
        "format": "1.2",
        "name": "_exmpl_band_gap",
        "label": "_exmpl_band_gap_structures",
    }
    assert definition["$id"].startswith("urn:uuid:")

    # The generated ID should be static, unless the definition is functionally changed
    assert (
        complete_property_definition(
            {**partial, "examples": [1.1], "x-optimade-implementation": {}},
            "_exmpl_band_gap",
            "structures",
        )["$id"]
        == definition["$id"]
    )
    assert (
        complete_property_definition(
            {**partial, "description": "The direct band gap."},
            "_exmpl_band_gap",
            "structures",
        )["$id"]
        != definition["$id"]
    )

    # Anything that is provided should be retained
    assert complete_property_definition(DEFINITION, "_exmpl_forces") == DEFINITION

    # The meta schema should follow the declared format
    partial["x-optimade-definition"] = {"format": "1.3"}
    assert complete_property_definition(partial, "_exmpl_band_gap")[
        "$schema"
    ] == get_meta_schema_url("1.3")

    with pytest.raises(ValidationError):
        complete_property_definition({"description": "The band gap."}, "_exmpl_gap")


def test_property_definition_from_description():
    definition = property_definition_from_description(
        {
            "name": "cell_volume",
            "description": "The volume of the cell.",
            "type": "float",
            "unit": "Ao3",
        },
        "_exmpl_cell_volume",
        "structures",
    )
    assert definition["x-optimade-type"] == "float"
    assert definition["type"] == ["number", "null"]
    assert definition["x-optimade-unit"] == "Ao3"
    assert definition["x-optimade-unit-definitions"][0]["standard"] == {
        "name": "ucum",
        "symbol": "Ao3",
    }
    assert "name" not in definition

    definition = property_definition_from_description(
        {"description": "The number of cells.", "type": "integer"}, "_exmpl_ncells"
    )
    assert definition["x-optimade-unit"] == "dimensionless"
    assert "x-optimade-unit-definitions" not in definition

    definition = property_definition_from_description(
        {"description": "The name of the cell.", "type": "string"}, "_exmpl_cell_name"
    )
    assert definition["x-optimade-unit"] == "inapplicable"

    # The keys of dictionaries cannot be described
    definition = property_definition_from_description(
        {"description": "A dictionary of unknown keys.", "type": "dictionary"},
        "_exmpl_dictionary",
    )
    assert definition["type"] == ["object", "null"]
    assert definition["properties"] == {}
    assert "$comment" in definition

    for bad_description in (
        {"description": "A list of unknown items.", "type": "list"},
        {"description": "A field with an unknown type."},
        {"type": "string"},
    ):
        with pytest.raises(ValueError):
            property_definition_from_description(bad_description, "_exmpl_bad")


def test_property_definition_from_json_schema():
    class Fit(BaseModel):
        method: Annotated[str | None, Field(description="The fitting method.")] = None
        residuals: Annotated[
            list[float], Field(description="The residuals.", max_length=3)
        ]

    class Model(BaseModel):
        fits: Annotated[list[Fit] | None, Field(description="The fits.")] = None

    field = Model.model_fields["fits"]
    schema = {
        "description": field.description,
        **TypeAdapter(field.annotation).json_schema(),
    }
    definition = property_definition_from_json_schema(
        schema, "_exmpl_fits", "structures"
    )
    assert definition["description"] == "The fits."
    assert definition["x-optimade-type"] == "list"
    assert definition["type"] == ["array", "null"]

    fit = definition["items"]
    assert fit["x-optimade-type"] == "dictionary"
    assert fit["type"] == ["object"]
    assert fit["required"] == ["residuals"]
    assert fit["properties"]["method"]["type"] == ["string", "null"]

    residuals = fit["properties"]["residuals"]
    assert residuals["x-optimade-type"] == "list"
    assert "maxItems" not in residuals
    assert residuals["items"] == {
        "x-optimade-type": "float",
        "x-optimade-unit": "dimensionless",
        "type": ["number"],
    }

    with pytest.raises(ValueError):
        property_definition_from_json_schema({"type": "string"}, "_exmpl_undescribed")

    with pytest.raises(ValueError):
        property_definition_from_json_schema(
            {"type": "array", "description": "A list of anything."}, "_exmpl_untyped"
        )
