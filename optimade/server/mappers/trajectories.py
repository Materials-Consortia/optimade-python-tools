from optimade.server.mappers.entries import BaseResourceMapper
from optimade.models.trajectories import TrajectoryResource, ReferenceStructure

__all__ = ("TrajectoryMapper",)


class TrajectoryMapper(BaseResourceMapper):
    # TODO add length aliases for trajectory specific properties
    LENGTH_ALIASES = (
        ("elements", "nelements"),
        ("element_ratios", "nelements"),
        ("cartesian_site_positions", "nsites"),
        ("species_at_sites", "nsites"),
    )
    # TODO: the field names may different than
    REFERENCE_STRUCTURE_FIELDS = [i for i in ReferenceStructure.__fields__.keys()]

    ENTRY_RESOURCE_CLASS = TrajectoryResource
