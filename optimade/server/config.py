import json
import os
import warnings
from enum import Enum
from pathlib import Path
from typing import Annotated, Any, Literal, Optional, Union

import yaml
from pydantic import AnyHttpUrl, Field, field_validator, model_validator
from pydantic.fields import FieldInfo
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

from optimade import __api_version__, __version__
from optimade.models import Implementation, Provider

DEFAULT_CONFIG_FILE_PATH: str = str(Path.home().joinpath(".optimade.json"))
"""Default configuration file path.

This variable is used as the fallback value if the environment variable
`OPTIMADE_CONFIG_FILE` is not set.

!!! note
    It is set to: `pathlib.Path.home()/.optimade.json`

    For Unix-based systems (Linux) this will be equivalent to `~/.optimade.json`.

"""


class LogLevel(Enum):
    """Replication of logging LogLevels

    - `notset`
    - `debug`
    - `info`
    - `warning`
    - `error`
    - `critical`

    """

    NOTSET = "notset"
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class SupportedBackend(Enum):
    """Enumeration of supported database backends

    - `elastic`: [Elasticsearch](https://www.elastic.co/).
    - `mongodb`: [MongoDB](https://www.mongodb.com/).
    - `mongomock`: Also MongoDB, but instead of using the
        [`pymongo`](https://pymongo.readthedocs.io/) driver to connect to a live Mongo
        database instance, this will use the
        [`mongomock`](https://github.com/mongomock/mongomock) driver, creating an
        in-memory database, which is mainly used for testing.

    """

    ELASTIC = "elastic"
    MONGODB = "mongodb"
    MONGOMOCK = "mongomock"


class ConfigFileSettingsSource(PydanticBaseSettingsSource):
    """Configuration file settings source.

    Based on the example in the
    [pydantic documentation](https://docs.pydantic.dev/latest/concepts/pydantic_settings/#customise-settings-sources),
    this class defines loading ServerConfig settings from a configuration file.

    The file must be of either type JSON or YML/YAML.
    """

    def get_field_value(
        self, field: FieldInfo, field_name: str
    ) -> tuple[Any, str, bool]:
        """Must be defined according to parent abstract class.

        It does not make sense to use it for this class, since 'extra' is set to
        'allow'. We will instead just parse and take every key/field specified in the
        config file.
        """
        raise NotImplementedError

    def parse_config_file(self) -> dict[str, Any]:
        """Parse the config file and return a dictionary of its content."""
        encoding = self.config.get("env_file_encoding")
        config_file = Path(os.getenv("OPTIMADE_CONFIG_FILE", DEFAULT_CONFIG_FILE_PATH))

        parsed_config_file = {}
        if config_file.is_file():
            config_file_content = config_file.read_text(encoding=encoding)

            try:
                parsed_config_file = json.loads(config_file_content)
            except json.JSONDecodeError as json_exc:
                try:
                    # This can essentially also load JSON files, as JSON is a subset of
                    # YAML v1, but I suspect it is not as rigorous
                    parsed_config_file = yaml.safe_load(config_file_content)
                except yaml.YAMLError as yaml_exc:
                    warnings.warn(
                        f"Unable to parse config file {config_file} as JSON or "
                        "YAML, using the default settings instead..\n"
                        f"Errors:\n  JSON:\n{json_exc}.\n\n  YAML:\n{yaml_exc}"
                    )
        else:
            warnings.warn(
                f"Unable to find config file at {config_file}, using the default "
                "settings instead."
            )

        if parsed_config_file is None:
            # This can happen if the yaml loading doesn't succeed properly, e.g., if
            # the file is empty.
            warnings.warn(
                f"Unable to load any settings from {config_file}, using the default "
                "settings instead."
            )
            parsed_config_file = {}

        if not isinstance(parsed_config_file, dict):
            warnings.warn(
                f"Unable to parse config file {config_file} as a dictionary, using "
                "the default settings instead."
            )
            parsed_config_file = {}

        return parsed_config_file

    def __call__(self) -> dict[str, Any]:
        return self.parse_config_file()


class ServerConfig(BaseSettings):
    """This class stores server config parameters in a way that
    can be easily extended for new config file types.
    """

    model_config = SettingsConfigDict(
        env_prefix="optimade_",
        extra="allow",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    debug: Annotated[
        bool,
        Field(
            description="Turns on Debug Mode for the OPTIMADE Server implementation",
        ),
    ] = False

    insert_test_data: Annotated[
        bool,
        Field(
            description=(
                "Insert test data into each collection on server initialisation. If true, "
                "the configured backend will be populated with test data on server start. "
                "Should be disabled for production usage."
            ),
        ),
    ] = True

    use_real_mongo: Annotated[
        Optional[bool],
        Field(description="DEPRECATED: force usage of MongoDB over any other backend."),
    ] = None

    database_backend: Annotated[
        SupportedBackend,
        Field(
            description="Which database backend to use out of the supported backends.",
        ),
    ] = SupportedBackend.MONGOMOCK

    elastic_hosts: Annotated[
        Optional[Union[str, list[str], dict[str, Any], list[dict[str, Any]]]],
        Field(
            description="Host settings to pass through to the `Elasticsearch` class."
        ),
    ] = None

    mongo_count_timeout: Annotated[
        int,
        Field(
            description=(
                "Number of seconds to allow MongoDB to perform a full database count "
                "before falling back to `null`. This operation can require a full COLLSCAN"
                " for empty queries which can be prohibitively slow if the database does "
                "not fit into the active set, hence a timeout can drastically speed-up "
                "response times."
            ),
        ),
    ] = 5

    mongo_database: Annotated[
        str, Field(description="Mongo database for collection data")
    ] = "optimade"
    mongo_uri: Annotated[str, Field(description="URI for the Mongo server")] = (
        "localhost:27017"
    )
    links_collection: Annotated[
        str, Field(description="Mongo collection name for /links endpoint resources")
    ] = "links"
    references_collection: Annotated[
        str,
        Field(
            description="Mongo collection name for /references endpoint resources",
        ),
    ] = "references"
    structures_collection: Annotated[
        str,
        Field(
            description="Mongo collection name for /structures endpoint resources",
        ),
    ] = "structures"
    page_limit: Annotated[
        int, Field(description="Default number of resources per page")
    ] = 20
    page_limit_max: Annotated[
        int, Field(description="Max allowed number of resources per page")
    ] = 500
    default_db: Annotated[
        str,
        Field(
            description=(
                "ID of /links endpoint resource for the chosen default OPTIMADE "
                "implementation (only relevant for the index meta-database)"
            ),
        ),
    ] = "test_server"
    root_path: Annotated[
        Optional[str],
        Field(
            description=(
                "Sets the FastAPI app `root_path` parameter. This can be used to serve the"
                " API under a path prefix behind a proxy or as a sub-application of "
                "another FastAPI app. See "
                "https://fastapi.tiangolo.com/advanced/sub-applications/#technical-details-root_path"
                " for details."
            ),
        ),
    ] = None
    base_url: Annotated[
        Optional[str], Field(description="Base URL for this implementation")
    ] = None
    implementation: Annotated[
        Implementation,
        Field(
            description="Introspective information about this OPTIMADE implementation",
        ),
    ] = Implementation(
        name="OPTIMADE Python Tools",
        version=__version__,
        source_url="https://github.com/Materials-Consortia/optimade-python-tools",
        maintainer={"email": "dev@optimade.org"},
        issue_tracker=(
            "https://github.com/Materials-Consortia/optimade-python-tools/issues"
        ),
        homepage="https://optimade.org/optimade-python-tools",
    )
    index_base_url: Annotated[
        Optional[AnyHttpUrl],
        Field(
            description=(
                "An optional link to the base URL for the index meta-database of the "
                "provider."
            ),
        ),
    ] = None
    provider: Annotated[
        Provider,
        Field(
            description=(
                "General information about the provider of this OPTIMADE implementation"
            ),
        ),
    ] = Provider(
        prefix="exmpl",
        name="Example provider",
        description=(
            "Provider used for examples, not to be assigned to a real database"
        ),
        homepage="https://example.com",
    )
    provider_fields: Annotated[
        dict[
            Literal["links", "references", "structures"],
            list[Union[str, dict[Literal["name", "type", "unit", "description"], str]]],
        ],
        Field(
            description=(
                "A list of additional fields to be served with the provider's prefix "
                "attached, broken down by endpoint."
            ),
        ),
    ] = {}
    aliases: Annotated[
        dict[Literal["links", "references", "structures"], dict[str, str]],
        Field(
            description=(
                "A mapping between field names in the database with their corresponding "
                "OPTIMADE field names, broken down by endpoint."
            ),
        ),
    ] = {}
    length_aliases: Annotated[
        dict[Literal["links", "references", "structures"], dict[str, str]],
        Field(
            description=(
                "A mapping between a list property (or otherwise) and an integer property "
                "that defines the length of that list, for example elements -> nelements. "
                "The standard aliases are applied first, so this dictionary must refer to "
                "the API fields, not the database fields."
            ),
        ),
    ] = {}
    index_links_path: Annotated[
        Path,
        Field(
            description=(
                "Absolute path to a JSON file containing the MongoDB collecton of links "
                "entries (documents) to serve under the /links endpoint of the index "
                "meta-database. NB! As suggested in the previous sentence, these will "
                "only be served when using a MongoDB-based backend."
            ),
        ),
    ] = Path(__file__).parent.joinpath("index_links.json")

    is_index: Annotated[
        Optional[bool],
        Field(
            description=(
                "A runtime setting to dynamically switch between index meta-database and "
                "normal OPTIMADE servers. Used for switching behaviour of e.g., "
                "`meta->optimade_schema` values in the response. Any provided value may "
                "be overridden when used with the reference server implementation."
            ),
        ),
    ] = False

    schema_url: Annotated[
        Optional[Union[str, AnyHttpUrl]],
        Field(
            description=(
                "A URL that will be provided in the `meta->schema` field for every response"
            ),
        ),
    ] = f"https://schemas.optimade.org/openapi/v{__api_version__}/optimade.json"

    custom_landing_page: Annotated[
        Optional[Union[str, Path]],
        Field(
            description=(
                "The location of a custom landing page (Jinja template) to use for the API."
            ),
        ),
    ] = None

    index_schema_url: Annotated[
        Optional[Union[str, AnyHttpUrl]],
        Field(
            description=(
                "A URL that will be provided in the `meta->schema` field for every "
                "response from the index meta-database."
            ),
        ),
    ] = f"https://schemas.optimade.org/openapi/v{__api_version__}/optimade_index.json"

    log_level: Annotated[
        LogLevel, Field(description="Logging level for the OPTIMADE server.")
    ] = LogLevel.INFO
    log_dir: Annotated[
        Path,
        Field(
            description="Folder in which log files will be saved.",
        ),
    ] = Path("/var/log/optimade/")
    validate_query_parameters: Annotated[
        Optional[bool],
        Field(
            description=(
                "If True, the server will check whether the query parameters given in the "
                "request are correct."
            ),
        ),
    ] = True

    validate_api_response: Annotated[
        Optional[bool],
        Field(
            description=(
                "If False, data from the database will not undergo validation before being"
                " emitted by the API, and only the mapping of aliases will occur."
            ),
        ),
    ] = True

    @field_validator("implementation", mode="before")
    @classmethod
    def set_implementation_version(cls, value: Any) -> dict[str, Any]:
        """Set defaults and modify bypassed value(s)"""
        if not isinstance(value, dict):
            if isinstance(value, Implementation):
                value = value.model_dump()
            else:
                raise TypeError(
                    f"Expected a dict or Implementation instance, got {type(value)}"
                )

        res = {"version": __version__}
        res.update(value)
        return res

    @model_validator(mode="after")
    def use_real_mongo_override(self) -> "ServerConfig":
        """Overrides the `database_backend` setting with MongoDB and
        raises a deprecation warning.
        """
        use_real_mongo = self.use_real_mongo

        # Remove from model
        del self.use_real_mongo

        # Remove from set of user-defined fields
        if "use_real_mongo" in self.model_fields_set:
            self.model_fields_set.remove("use_real_mongo")

        if use_real_mongo is not None:
            warnings.warn(
                "'use_real_mongo' is deprecated, please set the appropriate 'database_backend' "
                "instead.",
                DeprecationWarning,
            )

            if use_real_mongo:
                self.database_backend = SupportedBackend.MONGODB

        return self

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """
        **Priority of config settings sources**:

        1. Passed arguments upon initialization of
            [`ServerConfig`][optimade.server.config.ServerConfig].
        2. Environment variables, matching the syntax: `"OPTIMADE_"` or `"optimade_"` +
            `<config_name>`, e.g., `OPTIMADE_LOG_LEVEL=debug` or
            `optimade_log_dir=~/logs_dir/optimade/`.
        3. Configuration file (JSON/YAML) taken from:
            1. Environment variable `OPTIMADE_CONFIG_FILE`.
            2. Default location (see
                [DEFAULT_CONFIG_FILE_PATH][optimade.server.config.DEFAULT_CONFIG_FILE_PATH]).
        4. Settings from secret file (see
            [pydantic documentation](https://pydantic-docs.helpmanual.io/usage/settings/#secret-support)
            for more information).

        """
        return (
            init_settings,
            env_settings,
            ConfigFileSettingsSource(settings_cls),
            file_secret_settings,
        )


CONFIG: ServerConfig = ServerConfig()
"""This singleton loads the config from a hierarchy of sources (see
[`customise_sources`][optimade.server.config.ServerConfig.settings_customise_sources])
and makes it importable in the server code.
"""
