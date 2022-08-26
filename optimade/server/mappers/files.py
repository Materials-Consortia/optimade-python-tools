from optimade.server.mappers.entries import BaseResourceMapper
from optimade.models.files import FileResource

__all__ = ("FileMapper",)


class FileMapper(BaseResourceMapper):

    ENTRY_RESOURCE_CLASS = FileResource
