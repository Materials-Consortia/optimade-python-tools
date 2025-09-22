"""Tests for optimade.filtertransformers.BaseTransformer"""


def test_quantity_builder() -> None:
    from optimade.filtertransformers.base_transformer import BaseTransformer, Quantity
    from optimade.server.mappers import StructureMapper

    class DummyTransformer(BaseTransformer):
        pass

    class AwkwardMapper(StructureMapper):
        ALIASES = (("elements", "my_elements"), ("nelements", "nelem"))
        LENGTH_ALIASES = (
            ("chemsys", "nelements"),
            ("cartesian_site_positions", "nsites"),
            ("elements", "nelements"),
        )
        PROVIDER_FIELDS = ("chemsys",)

    m = AwkwardMapper()
    t = DummyTransformer(mapper=m)

    assert "_exmpl_chemsys" in t.quantities
    assert isinstance(t.quantities["_exmpl_chemsys"], Quantity)
    assert t.quantities["_exmpl_chemsys"].name == "_exmpl_chemsys"
    assert t.quantities["_exmpl_chemsys"].backend_field == "chemsys"

    assert isinstance(t.quantities["_exmpl_chemsys"].length_quantity, Quantity)
    assert t.quantities["_exmpl_chemsys"].length_quantity.name == "nelements"
    assert t.quantities["_exmpl_chemsys"].length_quantity.backend_field == "nelem"

    assert isinstance(t.quantities["elements"], Quantity)
    assert isinstance(t.quantities["elements"].length_quantity, Quantity)
    assert t.quantities["elements"].length_quantity.backend_field == "nelem"
