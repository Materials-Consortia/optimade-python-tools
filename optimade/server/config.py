import os
import json
from typing import Any, Optional
from configparser import ConfigParser
from pathlib import Path
from warnings import warn

from pydantic import BaseSettings

from optimade import __version__
from optimade.models import Implementation, Provider


class NoFallback(Exception):
    """No fallback value can be found."""


class ServerConfig(BaseSettings):
    """ This class stores server config parameters in a way that
    can be easily extended for new config file types.

    """

    use_real_mongo: bool = False
    mongo_database: str = "optimade"
    mongo_uri: str = "localhost:27017"
    links_collection: str = "links"
    references_collection: str = "references"
    structures_collection: str = "structures"
    page_limit: int = 20
    page_limit_max: int = 500
    default_db: str = "test_server"
    base_url: Optional[str] = None
    implementation: Implementation = Implementation()
    provider: Provider = Provider()

    index_links_path: Path = Path(__file__).parent.joinpath("index_links.json")

    class Config:
        env_file = ".optimade"
        env_prefix = "optimade_"
        fields = {
            "auth_key": {"env": "my_auth_key"},
            "redis_dsn": {"env": ["service_redis_dsn", "redis_url"]},
        }


CONFIG = ServerConfig()
