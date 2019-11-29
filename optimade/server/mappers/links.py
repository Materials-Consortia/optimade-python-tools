from .entries import ResourceMapper

__all__ = ("LinksMapper",)


class LinksMapper(ResourceMapper):

    ENDPOINT = "links"

    @classmethod
    def map_back(cls, doc: dict) -> dict:
        """Map properties from MongoDB to OPTiMaDe

        :param doc: A resource object in MongoDB format
        :type doc: dict

        :return: A resource object in OPTiMaDe format
        :rtype: dict
        """
        type_ = doc["type"]
        newdoc = super().map_back(doc)
        newdoc["type"] = type_
        return newdoc
