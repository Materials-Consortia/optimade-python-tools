from optimade.models.references import ReferenceResource
from optimade.server.mappers.entries import BaseResourceMapper

__all__ = ("ReferenceMapper",)


class ReferenceMapper(BaseResourceMapper):

    ENTRY_RESOURCE_CLASS = ReferenceResource
