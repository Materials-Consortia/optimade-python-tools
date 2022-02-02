from optimade.server.mappers.entries import BaseResourceMapper
from optimade.models.trajectories import TrajectoryResource

__all__ = ("TrajectoryMapper",)


class TrajectoryMapper(BaseResourceMapper):

    LENGTH_ALIASES = (
        ("elements", "nelements"),
        ("element_ratios", "nelements"),
        ("cartesian_site_positions", "nsites"),
        ("species_at_sites", "nsites"),
    )
    ENTRY_RESOURCE_CLASS = TrajectoryResource
