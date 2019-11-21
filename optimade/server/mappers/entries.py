import abc
from typing import Tuple
from optimade.server.config import CONFIG


__all__ = ("ResourceMapper",)


class ResourceMapper(metaclass=abc.ABCMeta):
    """Generic Resource Mapper"""

    ENDPOINT: str = ""
    ALIASES: Tuple[Tuple[str, str]] = ()

    @classmethod
    def all_aliases(cls) -> Tuple[Tuple[str, str]]:
        return (
            tuple(
                (CONFIG.provider["prefix"] + field, field)
                for field in CONFIG.provider_fields[cls.ENDPOINT]
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

    @abc.abstractclassmethod
    def map_back(cls, doc: dict) -> dict:
        """Map properties from MongoDB to OPTiMaDe

        :param doc: A resource object in MongoDB format
        :type doc: dict

        :return: A resource object in OPTiMaDe format
        :rtype: dict
        """
