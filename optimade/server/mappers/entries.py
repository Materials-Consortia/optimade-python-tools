from typing import Tuple
from optimade.server.config import CONFIG

__all__ = ("ResourceMapper",)


class ResourceMapper:
    """Generic Resource Mapper"""

    ENDPOINT: str = ""
    ALIASES: Tuple[Tuple[str, str]] = ()

    @classmethod
    def all_aliases(cls) -> Tuple[Tuple[str, str]]:
        return (
            tuple(
                (CONFIG.provider["prefix"] + field, field)
                for field in CONFIG.provider_fields.get(cls.ENDPOINT, {})
            )
            + cls.ALIASES
        )

    @classmethod
    def alias_for(cls, field: str) -> str:
        """Return aliased field name

        :param field: OPtiMaDe field name
        :type field: str

        :return: Aliased field as found in PROVIDER_ALIASES + ALIASES
        :rtype: str
        """
        return dict(cls.all_aliases()).get(field, field)

    @classmethod
    def map_back(cls, doc: dict) -> dict:
        """Map properties from MongoDB to OPTiMaDe

        :param doc: A resource object in MongoDB format
        :type doc: dict

        :return: A resource object in OPTiMaDe format
        :rtype: dict
        """
        if "_id" in doc:
            del doc["_id"]

        mapping = ((real, alias) for alias, real in cls.all_aliases())
        newdoc = {}
        reals = {real for alias, real in cls.all_aliases()}
        for k in doc:
            if k not in reals:
                newdoc[k] = doc[k]
        for real, alias in mapping:
            if real in doc:
                newdoc[alias] = doc[real]

        if "attributes" in newdoc:
            raise Exception("Will overwrite doc field!")
        attributes = newdoc.copy()

        top_level_entry_fields = {"id", "type", "relationships", "links"}
        for k in top_level_entry_fields:
            attributes.pop(k, None)
        for k in list(newdoc.keys()):
            if k not in top_level_entry_fields:
                del newdoc[k]

        newdoc["type"] = cls.ENDPOINT
        newdoc["attributes"] = attributes

        return newdoc
