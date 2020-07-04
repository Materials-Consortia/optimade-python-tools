import pytest

from optimade.server.mappers import BaseResourceMapper
from optimade.server.entry_collections import MongoCollection
from optimade.models import StructureResource


def test_disallowed_aliases():
    import mongomock

    class MyMapper(BaseResourceMapper):
        ALIASES = (("$and", "my_special_and"), ("not", "$not"))

    mapper = MyMapper()
    toy_collection = mongomock.MongoClient()["fake"]["fake"]
    with pytest.raises(RuntimeError):
        MongoCollection(toy_collection, StructureResource, mapper)


def test_property_aliases():
    class MyMapper(BaseResourceMapper):
        PROVIDER_FIELDS = ("dft_parameters", "test_field")
        LENGTH_ALIASES = (("_exmpl_test_field", "test_field_len"),)
        ALIASES = (("field", "completely_different_field"),)

    mapper = MyMapper()
    assert mapper.alias_for("_exmpl_dft_parameters") == "dft_parameters"
    assert mapper.alias_for("_exmpl_test_field") == "test_field"
    assert mapper.alias_for("field") == "completely_different_field"
    assert mapper.length_alias_for("_exmpl_test_field") == "test_field_len"
    assert mapper.length_alias_for("test_field") is None
    assert mapper.alias_for("test_field") == "test_field"

    # nested properties
    assert (
        mapper.alias_for("_exmpl_dft_parameters.nested.property")
        == "dft_parameters.nested.property"
    )
    assert (
        mapper.alias_for("_exmpl_dft_parameters.nested_property")
        == "dft_parameters.nested_property"
    )

    # test nonsensical query
    assert mapper.alias_for("_exmpl_test_field.") == "test_field."

    # test an awkward case that has no alias
    assert (
        mapper.alias_for("_exmpl_dft_parameters_dft_parameters.nested.property")
        == "_exmpl_dft_parameters_dft_parameters.nested.property"
    )
