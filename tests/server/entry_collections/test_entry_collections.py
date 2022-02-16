"""Test the EntryCollection abstract base class"""


def test_get_attribute_fields():
    """Test get_attribute_fields() method"""
    from optimade.models import (
        LinksResourceAttributes,
        ReferenceResourceAttributes,
        StructureResourceAttributes,
        TrajectoryResourceAttributes,
    )
    from optimade.server.routers import ENTRY_COLLECTIONS

    entry_name_attributes = {
        "links": LinksResourceAttributes,
        "references": ReferenceResourceAttributes,
        "structures": StructureResourceAttributes,
        "trajectories": TrajectoryResourceAttributes,
    }

    # Make sure we're hitting all collections
    assert set(entry_name_attributes.keys()) == set(ENTRY_COLLECTIONS.keys())

    for entry_name, attributes_model in entry_name_attributes.items():
        entry_collection_fields = set()
        for field in ENTRY_COLLECTIONS[entry_name].get_attribute_fields():
            if field[0] == "_":
                field = field[1:]
            entry_collection_fields.add(field)
        assert set(attributes_model.__fields__.keys()) == entry_collection_fields
