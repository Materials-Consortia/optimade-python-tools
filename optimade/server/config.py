import json
from typing import Any
from configparser import ConfigParser
from pathlib import Path
from warnings import warn

from optimade import __version__
from optimade.models import Implementation


class NoFallback(Exception):
    """No fallback value can be found."""


class Config:
    """Base class for loading config files and its parameters"""

    index_links_path: Path = Path(__file__).parent.joinpath("index_links.json")
    _path: Path = Path(__file__).parent.joinpath("config.ini")

    def __init__(self, server_cfg: Path = None):
        self._server = (
            Path().resolve().joinpath("server.cfg")
            if server_cfg is None
            else server_cfg
        )

    def __getattr__(self, name: str) -> Any:
        self._load_server_config()

        ftype = self._path.suffix[1:]  # Remove initial "."
        self.load(ftype)

        if name not in self.__dict__:
            raise AttributeError(
                f"'{self.__class__.__name__}' object has no attribute '{name}'"
            )

        return getattr(self, name)

    def _load_server_config(self):
        """Load cfg-file determining paths to server config files"""
        SECTION = "optimadeconfig"
        INDEX_LINKS_PATH = "INDEX_LINKS"
        SERVER_CONFIG_PATH = "CONFIG"

        server = ConfigParser()

        if self._server.exists():
            server.read(self._server)

        index_links_path = server.get(
            SECTION, INDEX_LINKS_PATH, fallback=str(self.index_links_path)
        )
        self.index_links_path = self._server.parent.joinpath(index_links_path).resolve()

        _path = server.get(SECTION, SERVER_CONFIG_PATH, fallback=str(self._path))
        self._path = self._server.parent.joinpath(_path).resolve()

        if not self._path.exists():
            raise ValueError(
                f'Cannot resolve {self._path}. Check the config-file exists. Note, "~" is not allowed.'
            )

        if not self.index_links_path.exists():
            warn(
                f'Cannot resolve {self.index_links_path}. Check the index_links.json file exists. Note, "~" is not allowed.'
            )

        if not self._server.exists():
            server.add_section(SECTION)
            server.set(SECTION, SERVER_CONFIG_PATH, str(self._path))
            server.set(SECTION, INDEX_LINKS_PATH, str(self.index_links_path))
            warn(f"No server.cfg file found, writing defaults to {self._server}")
            with open(self._server, "w") as f:
                server.write(f)

    def _get_load_func(self, format_name) -> Any:
        return getattr(self, f"load_from_{format_name}")

    def load(self, ftype: str = None):
        try:
            f = self._get_load_func(ftype)
        except AttributeError:
            raise NotImplementedError(
                f"load function for config format {ftype} is not implemented"
            )
        else:
            f()


class ServerConfig(Config):
    """ This class stores server config parameters in a way that
    can be easily extended for new config file types.

    """

    @staticmethod
    def _DEFAULTS(field: str) -> Any:
        res = {
            "use_real_mongo": False,
            "mongo_database": "optimade",
            "links_collection": "links",
            "references_collection": "references",
            "structures_collection": "structures",
            "page_limit": 20,
            "page_limit_max": 500,
            "default_db": "test_server",
            "base_url": None,
            "implementation": {
                "name": "Example implementation",
                "version": __version__,
                "source_url": "https://github.com/Materials-Consortia/optimade-python-tools",
                "maintainer": None,
            },
            "provider": {
                "prefix": "_exmpl_",
                "name": "Example provider",
                "description": "Provider used for examples, not to be assigned to a real database",
                "homepage": "https://example.com",
                "index_base_url": None,
            },
        }
        if field not in res:
            raise NoFallback(f"No fallback value found for '{field}'")
        return res[field]

    def load_from_ini(self):
        """ Load from the file "config.ini", if it exists. """
        config = ConfigParser()
        config.read(self._path)

        self.use_real_mongo = config.getboolean(
            "BACKEND", "USE_REAL_MONGO", fallback=self._DEFAULTS("use_real_mongo")
        )
        self.mongo_database = config.get(
            "BACKEND", "MONGO_DATABASE", fallback=self._DEFAULTS("mongo_database")
        )

        self.page_limit = config.getint(
            "SERVER", "PAGE_LIMIT", fallback=self._DEFAULTS("page_limit")
        )
        self.page_limit_max = config.getint(
            "SERVER", "PAGE_LIMIT_MAX", fallback=self._DEFAULTS("page_limit_max")
        )
        self.default_db = config.get(
            "SERVER", "DEFAULT_DB", fallback=self._DEFAULTS("default_db")
        )
        self.base_url = config.get(
            "SERVER", "BASE_URL", fallback=self._DEFAULTS("base_url")
        )

        # This is done in this way, since each field is OPTIONAL
        self.implementation = {}
        for field in Implementation.schema()["properties"]:
            value_config = config.get("IMPLEMENTATION", field, fallback=None)
            value_default = self._DEFAULTS("implementation")[field]
            if value_config is not None:
                self.implementation[field] = value_config
            elif value_default is not None:
                self.implementation[field] = value_default

        if "PROVIDER" in config.sections():
            self.provider = dict(config["PROVIDER"])
        else:
            self.provider = self._DEFAULTS("provider")

        self.provider_fields = {}
        for endpoint in {"links", "references", "structures"}:
            self.provider_fields[endpoint] = (
                list({field for field, _ in config[endpoint].items() if _ == ""})
                if endpoint in config
                else []
            )

            # MONGO collections
            setattr(
                self,
                f"{endpoint}_collection",
                config.get(
                    "BACKEND",
                    f"{endpoint.upper()}_COLLECTION",
                    fallback=self._DEFAULTS(f"{endpoint}_collection"),
                ),
            )

    def load_from_json(self):
        """ Load from the file "config.json", if it exists. """
        with open(self._path, "r") as f:
            config = json.load(f)

        self.use_real_mongo = bool(
            config.get("use_real_mongo", self._DEFAULTS("use_real_mongo"))
        )
        self.mongo_database = config.get(
            "mongo_database", self._DEFAULTS("mongo_database")
        )
        for endpoint in {"links", "references", "structures"}:
            setattr(
                self,
                f"{endpoint}_collection",
                config.get(
                    f"{endpoint}_collection", self._DEFAULTS(f"{endpoint}_collection")
                ),
            )

        self.page_limit = int(config.get("page_limit", self._DEFAULTS("page_limit")))
        self.page_limit_max = int(
            config.get("page_limit_max", self._DEFAULTS("page_limit_max"))
        )
        self.default_db = config.get("default_db", self._DEFAULTS("default_db"))
        self.base_url = config.get("base_url", self._DEFAULTS("base_url"))

        # This is done in this way, since each field is OPTIONAL
        self.implementation = config.get("implementation", {})
        for field in Implementation.schema()["properties"]:
            value_default = self._DEFAULTS("implementation")[field]
            if field in self.implementation:
                # Keep the config value
                pass
            elif value_default is not None:
                self.implementation[field] = value_default

        self.provider = config.get("provider", self._DEFAULTS("provider"))
        self.provider_fields = {}
        for endpoint in {"structures", "references"}:
            self.provider_fields[endpoint] = list(
                set(config.get("provider_fields", {}).get(endpoint, []))
            )


CONFIG = ServerConfig()
