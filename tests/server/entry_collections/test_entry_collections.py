"""Test the EntryCollection abstract base class"""


def test_get_attribute_fields():
    """Test get_attribute_fields() method"""
    from optimade.models import (
        LinksResourceAttributes,
        ReferenceResourceAttributes,
        StructureResourceAttributes,
    )
    from optimade.server.config import ServerConfig
    from optimade.server.entry_collections import create_entry_collections

    # get default config and entry collections
    config = ServerConfig()
    entry_collections = create_entry_collections(config)

    entry_name_attributes = {
        "links": LinksResourceAttributes,
        "references": ReferenceResourceAttributes,
        "structures": StructureResourceAttributes,
    }

    # Make sure we're hitting all collections
    assert set(entry_name_attributes.keys()) == set(entry_collections.keys())

    for entry_name, attributes_model in entry_name_attributes.items():
        assert (
            set(attributes_model.model_fields.keys())
            == entry_collections[entry_name].get_attribute_fields()
        )
