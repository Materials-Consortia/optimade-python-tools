from typing import Tuple
from optimade.server.config import CONFIG

__all__ = ("BaseResourceMapper",)


class BaseResourceMapper:
    """ Generic Resource Mapper that defines and performs the mapping
    between objects in the database and the resource objects defined by
    the specification.

    Attributes:
        ENDPOINT (str): defines the endpoint for which to apply this
            mapper.
        ALIASES (Tuple[Tuple[str, str]]): a tuple of aliases between
            OPTiMaDe field names and the field names in the database ,
            e.g. `(("elements", "custom_elements_field"))`.
        REQUIRED_FIELDS (set[str]): the set of fieldnames to return
            when mapping to the OPTiMaDe format.
        TOP_LEVEL_NON_ATTRIBUTES_FIELDS (set[str]): the set of top-level
            field names common to all endpoints.

    """

    ENDPOINT: str = ""
    ALIASES: Tuple[Tuple[str, str]] = ()
    REQUIRED_FIELDS: set = set()
    TOP_LEVEL_NON_ATTRIBUTES_FIELDS: set = {"id", "type", "relationships", "links"}

    @classmethod
    def all_aliases(cls) -> Tuple[Tuple[str, str]]:
        return (
            tuple(
                (CONFIG.provider["prefix"] + field, field)
                for field in CONFIG.provider_fields.get(cls.ENDPOINT, [])
            )
            + CONFIG.aliases.get(cls.ENDPOINT, ())
            + cls.ALIASES
        )

    @classmethod
    def alias_for(cls, field: str) -> str:
        """Return aliased field name

        :param field: OPTiMaDe field name
        :type field: str

        :return: Aliased field as found in PROVIDER_ALIASES + ALIASES
        :rtype: str
        """
        return dict(cls.all_aliases()).get(field, field)

    @classmethod
    def get_required_fields(cls) -> set:
        """Return set REQUIRED response fields"""
        res = cls.TOP_LEVEL_NON_ATTRIBUTES_FIELDS.copy()
        res.update(cls.REQUIRED_FIELDS)
        return res

    @classmethod
    def map_back(cls, doc: dict) -> dict:
        """Map properties from MongoDB to OPTiMaDe

        Starting from a MongoDB document ``doc``, map the DB fields to the corresponding OPTiMaDe fields.
        Then, the fields are all added to the top-level field "attributes",
        with the exception of other top-level fields, defined in ``cls.TOPLEVEL_NON_ATTRIBUTES_FIELDS``.
        All fields not in ``cls.TOPLEVEL_NON_ATTRIBUTES_FIELDS`` + "attributes" will be removed.
        Finally, the ``type`` is given the value of the specified ``cls.ENDPOINT``.

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
        for key in doc:
            if key not in reals:
                newdoc[key] = doc[key]
        for real, alias in mapping:
            if real in doc:
                newdoc[alias] = doc[real]

        if "attributes" in newdoc:
            raise Exception("Will overwrite doc field!")
        attributes = newdoc.copy()

        for field in cls.TOP_LEVEL_NON_ATTRIBUTES_FIELDS:
            value = attributes.pop(field, None)
            if value is not None:
                newdoc[field] = value
        for field in list(newdoc.keys()):
            if field not in cls.TOP_LEVEL_NON_ATTRIBUTES_FIELDS:
                del newdoc[field]

        newdoc["type"] = cls.ENDPOINT
        newdoc["attributes"] = attributes

        return newdoc
