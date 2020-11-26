from typing import Tuple, Optional

__all__ = ("BaseResourceMapper",)


class BaseResourceMapper:
    """
    Generic Resource Mapper that defines and performs the mapping
    between objects in the database and the resource objects defined by
    the specification.

    Attributes:
        ENDPOINT (str): defines the endpoint for which to apply this
            mapper.
        ALIASES (Tuple[Tuple[str, str]]): a tuple of aliases between
            OPTIMADE field names and the field names in the database ,
            e.g. `(("elements", "custom_elements_field"))`.
        LENGTH_ALIASES (Tuple[Tuple[str, str]]): a tuple of aliases between
            a field name and another field that defines its length, to be used
            when querying, e.g. `(("elements", "nelements"))`.
            e.g. `(("elements", "custom_elements_field"))`.
        PROVIDER_FIELDS (Tuple[str]): a tuple of extra field names that this
            mapper should support when querying with the database prefix.
        REQUIRED_FIELDS (set[str]): the set of fieldnames to return
            when mapping to the OPTIMADE format.
        TOP_LEVEL_NON_ATTRIBUTES_FIELDS (set[str]): the set of top-level
            field names common to all endpoints.

    """

    ENDPOINT: str = ""
    ALIASES: Tuple[Tuple[str, str]] = ()
    LENGTH_ALIASES: Tuple[Tuple[str, str]] = ()
    PROVIDER_FIELDS: Tuple[str] = ()
    REQUIRED_FIELDS: set = set()
    TOP_LEVEL_NON_ATTRIBUTES_FIELDS: set = {"id", "type", "relationships", "links"}

    @classmethod
    def all_aliases(cls) -> Tuple[Tuple[str, str]]:
        """Returns all of the associated aliases for this class,
        including those defined by the server config.

        Returns:
            A tuple of alias tuples.

        """
        from optimade.server.config import CONFIG

        return (
            tuple(
                (f"_{CONFIG.provider.prefix}_{field}", field)
                for field in CONFIG.provider_fields.get(cls.ENDPOINT, [])
            )
            + tuple(
                (f"_{CONFIG.provider.prefix}_{field}", field)
                for field in cls.PROVIDER_FIELDS
            )
            + tuple(CONFIG.aliases.get(cls.ENDPOINT, {}).items())
            + cls.ALIASES
        )

    @classmethod
    def all_length_aliases(cls) -> Tuple[Tuple[str, str]]:
        """Returns all of the associated length aliases for this class,
        including those defined by the server config.

        Returns:
            A tuple of length alias tuples.

        """
        from optimade.server.config import CONFIG

        return cls.LENGTH_ALIASES + tuple(
            CONFIG.length_aliases.get(cls.ENDPOINT, {}).items()
        )

    @classmethod
    def length_alias_for(cls, field: str) -> Optional[str]:
        """Returns the length alias for the particular field,
        or `None` if no such alias is found.

        Parameters:
            field: OPTIMADE field name.

        Returns:
            Aliased field as found in [`all_length_aliases()`][optimade.server.mappers.entries.BaseResourceMapper.all_length_aliases].

        """
        return dict(cls.all_length_aliases()).get(field, None)

    @classmethod
    def alias_for(cls, field: str) -> str:
        """Return aliased field name.

        Parameters:
            field: OPTIMADE field name.

        Returns:
            Aliased field as found in [`all_aliases()`][optimade.server.mappers.entries.BaseResourceMapper.all_aliases].

        """
        split = field.split(".")
        alias = dict(cls.all_aliases()).get(split[0], None)
        if alias is not None:
            return alias + ("." + ".".join(split[1:]) if len(split) > 1 else "")
        return field

    @classmethod
    def alias_of(cls, field: str) -> str:
        """Return de-aliased field name, if it exists,
        otherwise return the input field name.

        Args:
            field: Field name to be de-aliased.

        Returns:
            De-aliased field name, falling back to returning `field`.

        """
        field = field.split(".")[0]
        return {alias: real for real, alias in cls.all_aliases()}.get(field, field)

    @classmethod
    def get_required_fields(cls) -> set:
        """Get REQUIRED response fields.

        Returns:
            REQUIRED response fields.

        """
        res = cls.TOP_LEVEL_NON_ATTRIBUTES_FIELDS.copy()
        res.update(cls.REQUIRED_FIELDS)
        return res

    @classmethod
    def map_back(cls, doc: dict) -> dict:
        """Map properties from MongoDB to OPTIMADE.

        Starting from a MongoDB document `doc`, map the DB fields to the corresponding OPTIMADE fields.
        Then, the fields are all added to the top-level field "attributes",
        with the exception of other top-level fields, defined in `cls.TOP_LEVEL_NON_ATTRIBUTES_FIELDS`.
        All fields not in `cls.TOP_LEVEL_NON_ATTRIBUTES_FIELDS` + "attributes" will be removed.
        Finally, the `type` is given the value of the specified `cls.ENDPOINT`.

        Parameters:
            doc: A resource object in MongoDB format.

        Returns:
            A resource object in OPTIMADE format.

        """
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
