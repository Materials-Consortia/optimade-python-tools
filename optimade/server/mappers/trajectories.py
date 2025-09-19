from collections import Counter

from bson.objectid import ObjectId

from optimade.models.entries import EntryResourceAttributes
from optimade.models.structures import StructureResourceAttributes
from optimade.models.trajectories import TrajectoryResource
from optimade.server.config import CONFIG
from optimade.server.mappers.entries import BaseResourceMapper

__all__ = ("TrajectoryMapper",)


class TrajectoryMapper(BaseResourceMapper):
    # TODO add length aliases for trajectory specific properties
    LENGTH_ALIASES = (
        ("elements", "nelements"),
        ("element_ratios", "nelements"),
        ("cartesian_site_positions", "nsites"),
        ("species_at_sites", "nsites"),
    )
    #HIDDEN_FIELDS = ["_id"]

    # STANDARD_FIELDS = {
    #     "reference_frame",
    #     "nframes",
    #     "available_properties",
    # }.union(BaseResourceMapper.get_required_fields()).union(
    #     EntryResourceAttributes.model_fields.keys()
    # )
    ENTRY_RESOURCE_CLASS = TrajectoryResource
    ENDPOINT = "trajectories"

    # @classmethod
    # def map_back(cls, doc: dict) -> dict:
    #     atributes = { **doc }
    #     del atributes["id"]
    #     del atributes["_id"]
    #     mapped_doc = { "id": doc["id"], "type": "trajectories", "attributes": atributes }
    #     return mapped_doc
