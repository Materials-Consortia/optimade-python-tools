from .entries import BaseResourceMapper

__all__ = ("StructureMapper",)


class StructureMapper(BaseResourceMapper):

    ENDPOINT = "structures"

    LENGTH_ALIASES = (
        ("elements", "nelements"),
        ("element_ratios", "nelements"),
        ("cartesian_site_positions", "nsites"),
        ("species_at_sites", "nsites"),
    )
