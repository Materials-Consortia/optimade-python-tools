"""Tests for optimade.filtertransformers.BaseTransformer"""
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

    from optimade.server.mappers import BaseResourceMapper


def test_quantity_builder(mapper: "Callable[[str], type[BaseResourceMapper]]") -> None:
    from optimade.filtertransformers.base_transformer import BaseTransformer, Quantity

    class DummyTransformer(BaseTransformer):
        pass

    class AwkwardMapper(mapper("StructureMapper")):  # type: ignore[misc]
        ALIASES = (("elements", "my_elements"), ("nelements", "nelem"))
        LENGTH_ALIASES = (
            ("chemsys", "nelements"),
            ("cartesian_site_positions", "nsites"),
            ("elements", "nelements"),
        )
        PROVIDER_FIELDS = ("chemsys",)

    m = AwkwardMapper
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
