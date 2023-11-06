from optimade.models.partial_data import PartialDataResource
from optimade.server.mappers.entries import BaseResourceMapper

__all__ = ("PartialDataMapper",)


class PartialDataMapper(BaseResourceMapper):
    LENGTH_ALIASES = ()
    ENTRY_RESOURCE_CLASS = PartialDataResource
