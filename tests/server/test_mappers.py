import pytest

from optimade.models import StructureResource
from optimade.server.config import CONFIG

MAPPER = "BaseResourceMapper"


@pytest.mark.skipif(
    CONFIG.database_backend.value not in ("mongomock", "mongodb"),
    reason="Skipping mongo-related test when testing the elasticsearch backend.",
)
def test_disallowed_aliases(mapper):
    from optimade.server.entry_collections.mongo import MongoCollection

    class MyMapper(mapper(MAPPER)):
        ALIASES = (("$and", "my_special_and"), ("not", "$not"))

    mapper = MyMapper()
    with pytest.raises(RuntimeError):
        MongoCollection("fake", StructureResource, mapper, database="fake")


def test_property_aliases(mapper):
    class MyMapper(mapper(MAPPER)):
        PROVIDER_FIELDS = (
            "dft_parameters",
            "test_field",
            "database_specific_field",
            "species.oxidation_state",
        )
        LENGTH_ALIASES = (("_exmpl_test_field", "test_field_len"),)
        ALIASES = (
            ("field", "completely_different_field"),
            ("species", "particle_type"),
            ("species.name", "particles.class"),
            ("database_specific_field", "backend.subfield.sub_sub_field"),
        )
        ENTRY_RESOURCE_ATTRIBUTES = {
            "species": 42
        }  # This is not a proper value for ENTRY_RESOURCE_ATTRIBUTES but we need ut to test allowing database specific properties within optimade dictionary fields.

    mapper = MyMapper()
    assert mapper.get_backend_field("_exmpl_dft_parameters") == "dft_parameters"
    assert mapper.get_backend_field("_exmpl_test_field") == "test_field"
    assert mapper.get_backend_field("field") == "completely_different_field"
    assert mapper.get_backend_field("species.mass") == "particle_type.mass"
    assert (
        mapper.get_backend_field("species.oxidation_state")
        == "particle_type.oxidation_state"
    )
    assert mapper.get_backend_field("species.name") == "particles.class"
    assert (
        mapper.get_backend_field("_exmpl_database_specific_field")
        == "backend.subfield.sub_sub_field"
    )
    assert mapper.length_alias_for("_exmpl_test_field") == "test_field_len"
    assert mapper.length_alias_for("test_field") is None
    assert mapper.get_backend_field("test_field") == "test_field"
    with pytest.warns(DeprecationWarning):
        assert mapper.alias_for("test_field") == "test_field"

    assert mapper.get_optimade_field("dft_parameters") == "_exmpl_dft_parameters"
    assert mapper.get_optimade_field("test_field") == "_exmpl_test_field"
    assert mapper.get_optimade_field("completely_different_field") == "field"
    assert mapper.get_optimade_field("nonexistent_field") == "nonexistent_field"
    assert mapper.get_optimade_field("particles.class") == "species.name"
    assert mapper.get_optimade_field("particle_type.mass") == "species.mass"
    assert (
        mapper.get_optimade_field("backend.subfield.sub_sub_field")
        == "_exmpl_database_specific_field"
    )
    assert (
        mapper.get_optimade_field("particle_type.oxidation_state")
        == "species._exmpl_oxidation_state"
    )
    with pytest.warns(DeprecationWarning):
        assert mapper.alias_of("nonexistent_field") == "nonexistent_field"

    # nested properties
    assert (
        mapper.get_backend_field("_exmpl_dft_parameters.nested.property")
        == "dft_parameters.nested.property"
    )
    assert (
        mapper.get_backend_field("_exmpl_dft_parameters.nested_property")
        == "dft_parameters.nested_property"
    )

    # test nonsensical query
    assert mapper.get_backend_field("_exmpl_test_field.") == "test_field."

    # test an awkward case that has no alias
    assert (
        mapper.get_backend_field("_exmpl_dft_parameters_dft_parameters.nested.property")
        == "_exmpl_dft_parameters_dft_parameters.nested.property"
    )


def test_map_back_nested_field(mapper):
    class MyMapper(mapper(MAPPER)):
        ALIASES = (("some_field", "main_field.nested_field.field_we_need"),)

    mapper = MyMapper()
    input_dict = {
        "main_field": {
            "nested_field": {"field_we_need": 42, "other_field": 78},
            "another_nested_field": 89,
        },
        "secondary_field": 52,
    }
    output_dict = mapper.map_back(input_dict)
    assert output_dict["attributes"]["some_field"] == 42


def test_map_back_to_nested_field(mapper):
    class MyMapper(mapper(MAPPER)):
        ALIASES = (("some_field.subfield", "main_field.nested_field.field_we_need"),)

    mapper = MyMapper()
    input_dict = {
        "main_field": {
            "nested_field": {"field_we_need": 42, "other_field": 78},
            "another_nested_field": 89,
        },
        "secondary_field": 52,
    }
    output_dict = mapper.map_back(input_dict)
    assert output_dict["attributes"]["some_field"]["subfield"] == 42
