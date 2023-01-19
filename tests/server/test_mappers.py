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

    mapper = MyMapper
    with pytest.raises(RuntimeError):
        MongoCollection("fake", StructureResource, mapper, database="fake")


def test_property_aliases(mapper):
    class MyMapper(mapper(MAPPER)):
        PROVIDER_FIELDS = ("dft_parameters", "test_field")
        LENGTH_ALIASES = (("_exmpl_test_field", "test_field_len"),)
        ALIASES = (("field", "completely_different_field"),)

    mapper = MyMapper
    assert mapper.get_backend_field("_exmpl_dft_parameters") == "dft_parameters"
    assert mapper.get_backend_field("_exmpl_test_field") == "test_field"
    assert mapper.get_backend_field("field") == "completely_different_field"
    assert mapper.length_alias_for("_exmpl_test_field") == "test_field_len"
    assert mapper.length_alias_for("test_field") is None
    assert mapper.get_backend_field("test_field") == "test_field"
    with pytest.warns(DeprecationWarning):
        assert mapper.alias_for("test_field") == "test_field"

    assert mapper.get_optimade_field("dft_parameters") == "_exmpl_dft_parameters"
    assert mapper.get_optimade_field("test_field") == "_exmpl_test_field"
    assert mapper.get_optimade_field("completely_different_field") == "field"
    assert mapper.get_optimade_field("nonexistent_field") == "nonexistent_field"
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


def test_cached_mapper_properties(mapper):
    """Tests that alias caching both occurs, and is not effected
    by the presence of other mapper caches.
    """

    class MyMapper(mapper(MAPPER)):
        ALIASES = (("field", "completely_different_field"),)

    class MyOtherMapper(mapper(MAPPER)):
        ALIASES = (
            ("field", "completely_different_field2"),
            ("a", "b"),
        )

    assert MyMapper.get_backend_field("field") == "completely_different_field"
    hits = MyMapper.get_backend_field.cache_info().hits
    assert MyMapper.get_backend_field("field") == "completely_different_field"
    assert MyMapper.get_backend_field.cache_info().hits == hits + 1
    assert MyOtherMapper.get_backend_field("field") == "completely_different_field2"
    assert MyOtherMapper.get_backend_field.cache_info().hits == hits + 1
    assert MyOtherMapper.get_backend_field("field") == "completely_different_field2"
    assert MyOtherMapper.get_backend_field.cache_info().hits == hits + 2

    assert MyOtherMapper.get_backend_field("a") == "b"
    assert MyOtherMapper.get_backend_field.cache_info().hits == hits + 2
    assert MyOtherMapper.get_backend_field("a") == "b"
    assert MyOtherMapper.get_backend_field.cache_info().hits == hits + 3
    assert MyMapper.get_backend_field("a") == "a"


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
