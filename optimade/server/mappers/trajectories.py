from optimade.server.mappers.entries import BaseResourceMapper
from optimade.models.entries import EntryResourceAttributes
from optimade.models.trajectories import TrajectoryResource
from optimade.models.structures import StructureAttributes

__all__ = ("TrajectoryMapper",)


class TrajectoryMapper(BaseResourceMapper):
    # TODO add length aliases for trajectory specific properties
    LENGTH_ALIASES = (
        ("elements", "nelements"),
        ("element_ratios", "nelements"),
        ("cartesian_site_positions", "nsites"),
        ("species_at_sites", "nsites"),
    )
    HIDDEN_FIELDS = ["_hdf5file_path"]

    REFERENCE_STRUCTURE_FIELDS = list(StructureAttributes.__fields__.keys())
    STANDARD_FIELDS = (
        {"reference_structure", "reference_frame", "nframes", "available_properties"}
        .union(BaseResourceMapper.get_required_fields())
        .union(EntryResourceAttributes.__fields__.keys())
    )
    ENTRY_RESOURCE_CLASS = TrajectoryResource
