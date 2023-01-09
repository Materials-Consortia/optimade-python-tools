from optimade.models.files import FileResource
from optimade.server.mappers.entries import BaseResourceMapper

__all__ = ("FileMapper",)


class FileMapper(BaseResourceMapper):

    ENTRY_RESOURCE_CLASS = FileResource
