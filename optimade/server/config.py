import json
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
    mongo_collection = "structures"
    provider = "_exmpl_"
    page_limit = 500
    provider_fields = set()
    _path = Path(__file__).resolve().parent

    def load_from_ini(self):
        """ Load from the file "config.ini", if it exists. """

        config = ConfigParser()
        config.read(self._path.joinpath("config.ini"))

        self.use_real_mongo = config.getboolean(
            "DEFAULT", "USE_REAL_MONGO", fallback=self.use_real_mongo
        )
        self.page_limit = config.getint(
            "DEFAULT", "PAGE_LIMIT", fallback=self.page_limit
        )
        self.mongo_database = config.get(
            "DEFAULT", "MONGO_DATABASE", fallback=self.mongo_database
        )
        self.mongo_collection = config.get(
            "DEFAULT", "MONGO_COLLECTION", fallback=self.mongo_collection
        )
        self.provider = config.get("DEFAULT", "PROVIDER", fallback=self.provider)

        self.provider_fields = {
            field for field, _ in config["STRUCTURE"].items() if _ == ""
        }

    def load_from_json(self):
        """ Load from the file "config.json", if it exists. """

        with open(self._path.joinpath("config.json"), "r") as f:
            config = json.load(f)

        self.use_real_mongo = bool(config.get("use_real_mongo", self.use_real_mongo))
        self.page_limit = int(config.get("page_limit", self.page_limit))
        self.mongo_database = config.get("mongo_database", self.mongo_database)
        self.mongo_collection = config.get("mongo_collection", self.mongo_collection)
        self.provider = config.get("provider", self.provider)
        self.provider_fields = set(config.get("provider_fields", self.provider_fields))


CONFIG = ServerConfig()
