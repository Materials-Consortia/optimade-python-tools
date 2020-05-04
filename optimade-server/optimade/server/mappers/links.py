from .entries import BaseResourceMapper

__all__ = ("LinksMapper",)


class LinksMapper(BaseResourceMapper):

    ENDPOINT = "links"

    @classmethod
    def map_back(cls, doc: dict) -> dict:
        """Map properties from MongoDB to OPTIMADE

        :param doc: A resource object in MongoDB format
        :type doc: dict

        :return: A resource object in OPTIMADE format
        :rtype: dict
        """
        type_ = doc["type"]
        newdoc = super().map_back(doc)
        newdoc["type"] = type_
        return newdoc
