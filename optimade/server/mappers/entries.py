import warnings
from collections.abc import Iterable
from functools import cached_property
from typing import Any, Literal

from optimade.models.entries import EntryResource
from optimade.server.config import ServerConfig

__all__ = ("BaseResourceMapper",)


class BaseResourceMapper:
    """Instance-based Resource Mapper.

    Create one instance per CONFIG (and optionally per providers set).
    Subclasses still set class-level constants like ENTRY_RESOURCE_CLASS.
    """

    # class-level knobs remain
    ALIASES: tuple[tuple[str, str], ...] = ()
    LENGTH_ALIASES: tuple[tuple[str, str], ...] = ()
    PROVIDER_FIELDS: tuple[str, ...] = ()
    ENTRY_RESOURCE_CLASS: type["EntryResource"] = EntryResource
    RELATIONSHIP_ENTRY_TYPES: set[str] = {"references", "structures"}
    TOP_LEVEL_NON_ATTRIBUTES_FIELDS: set[str] = {"id", "type", "relationships", "links"}

    def __init__(self, config: ServerConfig | None = None):
        """
        Args:
            config: Server CONFIG-like object (must expose:
                .provider.prefix, .provider_fields, .aliases, .length_aliases)
        """
        if config is None:
            config = ServerConfig()
        self.config = config
        try:
            from optimade.server.data import providers as PROVIDERS  # type: ignore
        except (ImportError, ModuleNotFoundError):
            PROVIDERS = {}
        self.providers = PROVIDERS

        self.KNOWN_PROVIDER_PREFIXES: set[str] = {
            prov["id"] for prov in self.providers.get("data", [])
        }

    # ---- Computed, cached once per instance ----
    @cached_property
    def ENDPOINT(self) -> Literal["links", "references", "structures"]:
        endpoint = self.ENTRY_RESOURCE_CLASS.model_fields["type"].default
        if not endpoint or not isinstance(endpoint, str):
            raise ValueError("Type not set for this entry type!")
        return endpoint

    @cached_property
    def SUPPORTED_PREFIXES(self) -> set[str]:
        return {self.config.provider.prefix}

    @cached_property
    def all_aliases(self) -> tuple[tuple[str, str], ...]:
        cfg = self.config
        ep = self.ENDPOINT
        provider_fields = cfg.provider_fields.get(ep) or []

        provider_field_aliases_str = tuple(
            (f"_{cfg.provider.prefix}_{field}", field)
            if not field.startswith("_")
            else (field, field)
            for field in provider_fields
            if isinstance(field, str)
        )
        provider_field_aliases_dict = tuple(
            (f"_{cfg.provider.prefix}_{fd['name']}", fd["name"])
            if not fd["name"].startswith("_")
            else (fd["name"], fd["name"])
            for fd in provider_fields
            if isinstance(fd, dict)
        )
        explicit_provider_fields = tuple(
            (f"_{cfg.provider.prefix}_{field}", field)
            if not field.startswith("_")
            else (field, field)
            for field in self.PROVIDER_FIELDS
        )
        config_aliases = tuple(cfg.aliases.get(ep, {}).items())

        return (
            provider_field_aliases_str
            + provider_field_aliases_dict
            + explicit_provider_fields
            + config_aliases
            + self.ALIASES
        )

    @cached_property
    def all_length_aliases(self) -> tuple[tuple[str, str], ...]:
        return self.LENGTH_ALIASES + tuple(
            self.config.length_aliases.get(self.ENDPOINT, {}).items()
        )

    @cached_property
    def ENTRY_RESOURCE_ATTRIBUTES_MAP(self) -> dict[str, Any]:
        from optimade.server.schemas import retrieve_queryable_properties

        return retrieve_queryable_properties(self.ENTRY_RESOURCE_CLASS)

    @cached_property
    def ALL_ATTRIBUTES(self) -> set[str]:
        cfg = self.config
        ep = self.ENDPOINT
        pf = cfg.provider_fields.get(ep, ())

        attrs = set(self.ENTRY_RESOURCE_ATTRIBUTES_MAP)
        attrs.update(
            self.get_optimade_field(field) for field in pf if isinstance(field, str)
        )
        attrs.update(
            self.get_optimade_field(field["name"])
            for field in pf
            if isinstance(field, dict)
        )
        attrs.update(self.get_optimade_field(field) for field in self.PROVIDER_FIELDS)
        return attrs

    # ---- Instance methods that use the cached properties ----
    def length_alias_for(self, field: str) -> str | None:
        return dict(self.all_length_aliases).get(field)

    def get_backend_field(self, optimade_field: str) -> str:
        split = optimade_field.split(".")
        alias = dict(self.all_aliases).get(split[0])
        if alias is not None:
            return alias + ("." + ".".join(split[1:]) if len(split) > 1 else "")
        return optimade_field

    def get_optimade_field(self, backend_field: str) -> str:
        return {alias: real for real, alias in self.all_aliases}.get(
            backend_field, backend_field
        )

    def alias_for(self, field: str) -> str:
        warnings.warn(
            "`.alias_for(...)` is deprecated; use `.get_backend_field(...)`.",
            DeprecationWarning,
        )
        return self.get_backend_field(field)

    def alias_of(self, field: str) -> str:
        warnings.warn(
            "`.alias_of(...)` is deprecated; use `.get_optimade_field(...)`.",
            DeprecationWarning,
        )
        return self.get_optimade_field(field)

    def get_required_fields(self) -> set[str]:
        return self.TOP_LEVEL_NON_ATTRIBUTES_FIELDS

    def map_back(self, doc: dict) -> dict:
        mapping = ((real, alias) for alias, real in self.all_aliases)
        newdoc = {}
        reals = {real for _, real in self.all_aliases}

        for key in doc:
            if key not in reals:
                newdoc[key] = doc[key]
        for real, alias in mapping:
            if real in doc:
                newdoc[alias] = doc[real]

        if "attributes" in newdoc:
            raise Exception("Will overwrite doc field!")
        attributes = newdoc.copy()

        for field in self.TOP_LEVEL_NON_ATTRIBUTES_FIELDS:
            value = attributes.pop(field, None)
            if value is not None:
                newdoc[field] = value
        for field in list(newdoc.keys()):
            if field not in self.TOP_LEVEL_NON_ATTRIBUTES_FIELDS:
                del newdoc[field]

        newdoc["type"] = self.ENDPOINT
        newdoc["attributes"] = attributes
        return newdoc

    def deserialize(self, results: dict | Iterable[dict]):
        if isinstance(results, dict):
            return self.ENTRY_RESOURCE_CLASS(**self.map_back(results))
        return [self.ENTRY_RESOURCE_CLASS(**self.map_back(doc)) for doc in results]
