import pytest

from optimade.models import StructureResource
from optimade.server.config import ServerConfig
from optimade.server.mappers import BaseResourceMapper

CONFIG = ServerConfig()


@pytest.mark.skipif(
    CONFIG.database_backend.value not in ("mongomock", "mongodb"),
    reason="Skipping mongo-related test when testing the elasticsearch backend.",
)
def test_disallowed_aliases():
    from optimade.server.entry_collections.mongo import MongoCollection

    class MyMapper(BaseResourceMapper):
        ENTRY_RESOURCE_CLASS = StructureResource
        ALIASES = (("$and", "my_special_and"), ("not", "$not"))

    mapper = MyMapper()
    with pytest.raises(RuntimeError):
        MongoCollection("fake", StructureResource, mapper, config=CONFIG)


def test_property_aliases():
    class MyMapper(BaseResourceMapper):
        ENTRY_RESOURCE_CLASS = StructureResource
        PROVIDER_FIELDS = ("dft_parameters", "test_field")
        LENGTH_ALIASES = (("_exmpl_test_field", "test_field_len"),)
        ALIASES = (("field", "completely_different_field"),)

    mapper = MyMapper()
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


def test_cached_mapper_properties():
    """Tests that alias caching both occurs, and is not effected
    by the presence of other mapper caches.
    """

    class MyMapper(BaseResourceMapper):
        ENTRY_RESOURCE_CLASS = StructureResource
        ALIASES = (("field", "completely_different_field"),)

    class MyOtherMapper(BaseResourceMapper):
        ENTRY_RESOURCE_CLASS = StructureResource
        ALIASES = (
            ("field", "completely_different_field2"),
            ("a", "b"),
        )

    m1 = MyMapper()
    m2 = MyOtherMapper()
    assert m1.get_backend_field("field") == "completely_different_field"
    assert m1.get_backend_field("field") == "completely_different_field"
    assert m2.get_backend_field("field") == "completely_different_field2"
    assert m2.get_backend_field("field") == "completely_different_field2"

    assert m2.get_backend_field("a") == "b"
    assert m2.get_backend_field("a") == "b"
    assert m1.get_backend_field("a") == "a"
