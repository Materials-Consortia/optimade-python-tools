import json
from typing import Dict, Set
from configparser import ConfigParser
from pathlib import Path


class Config:
    """Base class for loading config files and its parameters"""

    ftype = "ini"

    def __init__(self, ftype: str = None):
        ftype = self.ftype if ftype is None else ftype
        self.load(ftype)

    def _get_load_func(self, format_name):
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

    use_real_mongo = False
    mongo_database = "optimade"
    structures_collection = "structures"
    references_collection = "references"

    page_limit = 500
    version = "0.10.0"

    provider = {
        "prefix": "_exmpl_",
        "name": "Example provider",
        "description": "Provider used for examples, not to be assigned to a real database",
        "homepage": "http://example.com",
        "index_base_url": "http://example.com/optimade/index",
    }
    provider_fields: Dict[str, Set] = {}
    _path = Path(__file__).resolve().parent

    def load_from_ini(self):
        """ Load from the file "config.ini", if it exists. """

        config = ConfigParser()
        config.read(self._path.joinpath("config.ini"))

        self.use_real_mongo = config.getboolean(
            "BACKEND", "USE_REAL_MONGO", fallback=self.use_real_mongo
        )
        self.mongo_database = config.get(
            "BACKEND", "MONGO_DATABASE", fallback=self.mongo_database
        )

        self.page_limit = config.getint(
            "IMPLEMENTATION", "PAGE_LIMIT", fallback=self.page_limit
        )
        self.version = config.get("IMPLEMENTATION", "VERSION", fallback=self.version)

        if "PROVIDER" in config.sections():
            self.provider = dict(config["PROVIDER"])

        self.provider_fields = {}
        for endpoint in {"structures", "references"}:
            self.provider_fields[endpoint] = (
                {field for field, _ in config[endpoint].items() if _ == ""}
                if endpoint in config
                else {}
            )

            # MONGO collections
            setattr(
                self,
                f"{endpoint}_collection",
                config.get(
                    "BACKEND",
                    f"{endpoint.upper()}_COLLECTION",
                    fallback=getattr(self, f"{endpoint}_collection"),
                ),
            )

    def load_from_json(self):
        """ Load from the file "config.json", if it exists. """

        with open(self._path.joinpath("config.json"), "r") as f:
            config = json.load(f)

        self.use_real_mongo = bool(config.get("use_real_mongo", self.use_real_mongo))
        self.mongo_database = config.get("mongo_database", self.mongo_database)
        for endpoint in {"structures", "references"}:
            setattr(
                self,
                f"{endpoint}_collection",
                config.get(f"{endpoint}_collection"),
                getattr(self, f"{endpoint}_collection"),
            )

        self.page_limit = int(config.get("page_limit", self.page_limit))
        self.version = config.get("version", self.version)

        self.provider = config.get("provider", self.provider)
        self.provider_fields = set(config.get("provider_fields", self.provider_fields))


CONFIG = ServerConfig()
