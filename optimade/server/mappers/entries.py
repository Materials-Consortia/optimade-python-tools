from typing import Tuple, Optional, Type, Set, Dict, Any, List, Iterable
from functools import lru_cache
import warnings
from optimade.server.config import CONFIG
from optimade.models.entries import EntryResource
from optimade.utils import (
    write_to_nested_dict,
    read_from_nested_dict,
    remove_from_nested_dict,
)

__all__ = ("BaseResourceMapper",)


class classproperty(property):
    """A simple extension of the property decorator that binds to types
    rather than instances.

    Modelled on this [StackOverflow answer](https://stackoverflow.com/a/5192374)
    with some tweaks to allow mkdocstrings to do its thing.

    """

    def __init__(self, func):
        self.__name__ = func.__name__
        self.__module__ = func.__module__
        self.__doc__ = func.__doc__
        self.__wrapped__ = func

    def __get__(self, _, owner):
        return self.__wrapped__(owner)


class BaseResourceMapper:
    """
    Generic Resource Mapper that defines and performs the mapping
    between objects in the database and the resource objects defined by
    the specification.

    Attributes:
        ALIASES: a tuple of aliases between
            OPTIMADE field names and the field names in the database ,
            e.g. `(("elements", "custom_elements_field"))`.
        LENGTH_ALIASES: a tuple of aliases between
            a field name and another field that defines its length, to be used
            when querying, e.g. `(("elements", "nelements"))`.
            e.g. `(("elements", "custom_elements_field"))`.
        ENTRY_RESOURCE_CLASS: The entry type that this mapper corresponds to.
        PROVIDER_FIELDS: a tuple of extra field names that this
            mapper should support when querying with the database prefix.
        TOP_LEVEL_NON_ATTRIBUTES_FIELDS: the set of top-level
            field names common to all endpoints.
        SUPPORTED_PREFIXES: The set of prefixes registered by this mapper.
        ALL_ATTRIBUTES: The set of attributes defined across the entry
            resource class and the server configuration.
        ENTRY_RESOURCE_ATTRIBUTES: A dictionary of attributes and their definitions
            defined by the schema of the entry resource class.
        ENDPOINT: The expected endpoint name for this resource, as defined by
            the `type` in the schema of the entry resource class.

    """

    try:
        from optimade.server.data import (
            providers as PROVIDERS,
        )  # pylint: disable=no-name-in-module
    except (ImportError, ModuleNotFoundError):
        PROVIDERS = {}

    KNOWN_PROVIDER_PREFIXES: Set[str] = set(
        prov["id"] for prov in PROVIDERS.get("data", [])
    )
    ALIASES: Tuple[Tuple[str, str]] = ()
    LENGTH_ALIASES: Tuple[Tuple[str, str]] = ()
    PROVIDER_FIELDS: Tuple[str] = ()
    ENTRY_RESOURCE_CLASS: Type[EntryResource] = EntryResource
    RELATIONSHIP_ENTRY_TYPES: Set[str] = {"references", "structures"}
    TOP_LEVEL_NON_ATTRIBUTES_FIELDS: Set[str] = {"id", "type", "relationships", "links"}
    SUPPORTED_PREFIXES: Set[str]
    ALL_ATTRIBUTES: Set[str]
    ENTRY_RESOURCE_ATTRIBUTES: Dict[str, Any]
    ENDPOINT: str

    @classmethod
    @lru_cache(maxsize=1)
    def all_prefixed_fields(cls) -> Iterable[Tuple[str, str]]:
        """Returns all of the prefixed, unprefixed field name pairs,
        including those defined by the server config. The first member
        of each tuple is the prefixed field name, the second
        is the field name as presented in the optimade database without prefix.

        Returns:
            A list of alias tuples.

        """
        field_list = (
            [
                field
                for field in CONFIG.provider_fields.get(cls.ENDPOINT, [])
                if isinstance(field, str)
            ]
            + [
                field["name"]
                for field in CONFIG.provider_fields.get(cls.ENDPOINT, [])
                if isinstance(field, dict)
            ]
            + list(cls.PROVIDER_FIELDS)
        )
        prefixed_field_pairs = []
        for field in field_list:
            split_field = field.split(
                ".", 1
            )  # For now I assume there are no nested dictionaries for the official Optimade fields
            if split_field[0] in cls.ENTRY_RESOURCE_ATTRIBUTES:
                prefixed_field_pairs.append(
                    (
                        f"{split_field[0]}._{CONFIG.provider.prefix}_{split_field[1]}",
                        field,
                    )
                )
            else:
                prefixed_field_pairs.append(
                    (f"_{CONFIG.provider.prefix}_{field}", field)
                )
        return prefixed_field_pairs

    @classmethod
    @lru_cache(maxsize=1)
    def all_aliases(cls) -> Iterable[Tuple[str, str]]:
        """Returns all of the associated aliases for this entry type,
        including those defined by the server config. The first member
        of each tuple is the field name as presented in the optimade database without prefix, the second
        is the backend-specific field name.

        Returns:
            A tuple of alias tuples.

        """

        return tuple(CONFIG.aliases.get(cls.ENDPOINT, {}).items()) + cls.ALIASES

    @classproperty
    @lru_cache(maxsize=1)
    def SUPPORTED_PREFIXES(cls) -> Set[str]:
        """A set of prefixes handled by this entry type.

        !!! note
            This implementation only includes the provider prefix,
            but in the future this property may be extended to include other
            namespaces (for serving fields from, e.g., other providers or
            domain-specific terms).

        """

        return {CONFIG.provider.prefix}

    @classproperty
    def ALL_ATTRIBUTES(cls) -> Set[str]:
        """Returns all attributes served by this entry."""

        return (
            set(cls.ENTRY_RESOURCE_ATTRIBUTES)
            .union(
                cls.get_optimade_field(field)
                for field in CONFIG.provider_fields.get(cls.ENDPOINT, ())
                if isinstance(field, str)
            )
            .union(
                cls.get_optimade_field(field["name"])
                for field in CONFIG.provider_fields.get(cls.ENDPOINT, ())
                if isinstance(field, dict)
            )
            .union(set(cls.get_optimade_field(field) for field in cls.PROVIDER_FIELDS))
        )

    @classproperty
    def ENTRY_RESOURCE_ATTRIBUTES(cls) -> Dict[str, Any]:
        """Returns the dictionary of attributes defined by the underlying entry resource class."""
        from optimade.server.schemas import retrieve_queryable_properties

        return retrieve_queryable_properties(cls.ENTRY_RESOURCE_CLASS.schema())

    @classproperty
    @lru_cache(maxsize=1)
    def ENDPOINT(cls) -> str:
        """Returns the expected endpoint for this mapper, corresponding
        to the `type` property of the resource class.

        """
        return (
            cls.ENTRY_RESOURCE_CLASS.schema()
            .get("properties", {})
            .get("type", {})
            .get("default", "")
        )

    @classmethod
    @lru_cache(maxsize=1)
    def all_length_aliases(cls) -> Iterable[Tuple[str, str]]:
        """Returns all of the associated length aliases for this class,
        including those defined by the server config.

        Returns:
            A tuple of length alias tuples.

        """

        return cls.LENGTH_ALIASES + tuple(
            CONFIG.length_aliases.get(cls.ENDPOINT, {}).items()
        )

    @classmethod
    @lru_cache(maxsize=128)
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
    def get_map_field_from_dict(cls, field: str, aliases: dict):
        """Replaces (part of) the field_name "field" with the matching field in the dictionary dict"
        It first tries to find the entire field name(incl. subfields(which are separated by:".")) in the dictionary.
        If it is not present it removes the deepest nesting level and checks again.
        If the field occurs in the dictionary it is replaced by the value in the dictionary.
        Any unmatched subfields are appended.
        """
        split = field.split(".")
        for i in range(len(split), 0, -1):
            field_path = ".".join(split[0:i])
            if field_path in aliases:
                field = aliases.get(field_path)
                if split[i:]:
                    field += "." + ".".join(split[i:])
                break
        return field

    @classmethod
    @lru_cache(maxsize=128)
    def get_backend_field(cls, optimade_field: str) -> str:
        """Return the field name configured for the particular
        underlying database for the passed OPTIMADE field name, that would
        be used in an API filter.

        Aliases are read from
        [`all_aliases()`][optimade.server.mappers.entries.BaseResourceMapper.all_aliases].

        If a dot-separated field is provided, the mapper first looks for that field.
        If it is not present in the aliases it repeats the search with one nesting level less untill the field is found.
        If the field is not found, the unmodified `optimade_field` is returned.

        This means for an (OPTIMADE, DB) alias of (`species`, `kinds`), `get_backend_fields("species.mass")`
        will return `kinds.mass` as there is no specific entry for "species.mass" in the aliases.

        Arguments:
            optimade_field: The OPTIMADE field to attempt to map to the backend-specific field.

        Examples:
            >>> get_backend_field("chemical_formula_anonymous")
            'formula_anon'
            >>> get_backend_field("formula_anon")
            'formula_anon'
            >>> get_backend_field("_exmpl_custom_provider_field")
            'custom_provider_field'

        Returns:
            The mapped field name to be used in the query to the backend.

        """
        prefixed = dict(cls.all_prefixed_fields())
        optimade_field = cls.get_map_field_from_dict(optimade_field, prefixed)
        return cls.get_map_field_from_dict(optimade_field, dict(cls.all_aliases()))

    @classmethod
    @lru_cache(maxsize=128)
    def alias_for(cls, field: str) -> str:
        """Return aliased field name.

        !!! warning "Deprecated"
            This method is deprecated could be removed without further warning. Please use
            [`get_backend_field()`][optimade.server.mappers.entries.BaseResourceMapper.get_backend_field].

        Parameters:
            field: OPTIMADE field name.

        Returns:
            Aliased field as found in [`all_aliases()`][optimade.server.mappers.entries.BaseResourceMapper.all_aliases].

        """
        warnings.warn(
            "The `.alias_for(...)` method is deprecated, please use `.get_backend_field(...)`.",
            DeprecationWarning,
        )
        return cls.get_backend_field(field)

    @classmethod
    @lru_cache(maxsize=128)
    def get_optimade_field(cls, backend_field: str) -> str:
        """Return the corresponding OPTIMADE field name for the underlying database field,
        ready to be used to construct the OPTIMADE-compliant JSON response.
        !!Warning!! Incase a backend_field maps to multiple OPTIMADE fields, only one of the fields is returned.

        Aliases are read from
        [`all_aliases()`][optimade.server.mappers.entries.BaseResourceMapper.all_aliases].
        [`all_prefixed_fields()`][optimade.server.mappers.entries.BaseResourceMapper.all_prefixed_fields]

        Arguments:
            backend_field: The backend field to attempt to map to an OPTIMADE field.

        Examples:
            >>> get_optimade_field("chemical_formula_anonymous")
            'chemical_formula_anonymous'
            >>> get_optimade_field("formula_anon")
            'chemical_formula_anonymous'
            >>> get_optimade_field("custom_provider_field")
            '_exmpl_custom_provider_field'

        Returns:
            The mapped field name to be used in an OPTIMADE-compliant response.

        """
        # first map the property back to the field as presented in the optimade database.
        inv_alias_dict = dict((real, alias) for alias, real in cls.all_aliases())
        backend_field = cls.get_map_field_from_dict(backend_field, inv_alias_dict)
        inv_prefix_dict = dict(
            (real, alias) for alias, real in cls.all_prefixed_fields()
        )
        return cls.get_map_field_from_dict(backend_field, inv_prefix_dict)

    @classmethod
    @lru_cache(maxsize=128)
    def alias_of(cls, field: str) -> str:
        """Return de-aliased field name, if it exists,
        otherwise return the input field name.

        !!! warning "Deprecated"
            This method is deprecated could be removed without further warning. Please use
            [`get_optimade_field()`][optimade.server.mappers.entries.BaseResourceMapper.get_optimade_field].

        Parameters:
            field: Field name to be de-aliased.

        Returns:
            De-aliased field name, falling back to returning `field`.

        """
        warnings.warn(
            "The `.alias_of(...)` method is deprecated, please use `.get_optimade_field(...)`.",
            DeprecationWarning,
        )
        return cls.get_optimade_field(field)

    @classmethod
    @lru_cache(maxsize=1)
    def get_required_fields(cls) -> set:
        """Get REQUIRED response fields.

        Returns:
            REQUIRED response fields.

        """
        return cls.TOP_LEVEL_NON_ATTRIBUTES_FIELDS

    @classmethod
    def map_back(cls, doc: dict) -> dict:
        """Map properties in a dictionary to the OPTIMADE fields.

        Starting from a document `doc`, map the DB fields to the corresponding OPTIMADE fields.
        Then, the fields are all added to the top-level field "attributes",
        with the exception of other top-level fields, defined in `cls.TOP_LEVEL_NON_ATTRIBUTES_FIELDS`.
        All fields not in `cls.TOP_LEVEL_NON_ATTRIBUTES_FIELDS` + "attributes" will be removed.
        Finally, the `type` is given the value of the specified `cls.ENDPOINT`.

        Parameters:
            doc: A resource object.

        Returns:
            A resource object in OPTIMADE format.

        """
        newdoc = cls.add_alias_and_prefix(doc)

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

    @classmethod
    def add_alias_and_prefix(cls, doc: dict) -> dict:
        """Converts a dictionary with field names that match the backend database with the field names that are presented in the OPTIMADE database.
        The way these fields are converted is read from:
        [`all_aliases()`][optimade.server.mappers.entries.BaseResourceMapper.all_aliases].
        [`all_prefixed_fields()`][optimade.server.mappers.entries.BaseResourceMapper.all_prefixed_fields]

        Parameters:
            doc: A dictionary with the backend fields.

        Returns:
            A dictionary with the fieldnames as presented by OPTIMADE
        """
        newdoc = {}
        mod_doc = doc.copy()
        # First apply all the aliases (They are sorted so the deepest nesting level occurs first.)
        sorted_aliases = sorted(cls.all_aliases(), key=lambda ele: ele[0], reverse=True)
        for alias, real in sorted_aliases:
            value, found = read_from_nested_dict(mod_doc, real)
            if not found:
                # Some backend fields are used for more than one optimade field. As they are deleted from mod_doc the first time they are mapped we need a backup option to read the data.
                value, found = read_from_nested_dict(doc, real)
            if found:
                write_to_nested_dict(newdoc, alias, value)
                remove_from_nested_dict(mod_doc, real)
        # move fields without alias to new doc
        newdoc.update(mod_doc)
        # apply prefixes
        for prefixed_field, unprefixed_field in cls.all_prefixed_fields():
            value, found = read_from_nested_dict(newdoc, unprefixed_field)
            if found:
                write_to_nested_dict(newdoc, prefixed_field, value)
                remove_from_nested_dict(newdoc, unprefixed_field)

        return newdoc

    @classmethod
    def deserialize(cls, results: Iterable[dict]) -> List[EntryResource]:
        return [cls.ENTRY_RESOURCE_CLASS(**result) for result in results]
