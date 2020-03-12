import os
import json
from typing import Any, Optional, Dict, List
from typing_extensions import Literal
from configparser import ConfigParser
from pathlib import Path
from warnings import warn

from pydantic import BaseSettings, root_validator

from optimade import __version__
from optimade.models import Implementation, Provider


class NoFallback(Exception):
    """No fallback value can be found."""


class ServerConfig(BaseSettings):
    """ This class stores server config parameters in a way that
    can be easily extended for new config file types.

    """
    debug: bool = False
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
    implementation: Implementation = Implementation(
        name="Example implementation",
        version=__version__,
        source_url="https://github.com/Materials-Consortia/optimade-python-tools",
        maintainer=None,
    )
    provider: Provider = Provider(
        prefix="_exmpl_",
        name="Example provider",
        description="Provider used for examples, not to be assigned to a real database",
        homepage="https://example.com",
        index_base_url=None,
    )
    provider_fields: Dict[Literal["links", "references", "structures"], List[str]] = {}
    aliases: Dict[Literal["links", "references", "structures"], Dict[str, str]] = {}

    index_links_path: Path = Path(__file__).parent.joinpath("index_links.json")

    class Config:
        env_file = ".optimade.json"
        env_prefix = "optimade_"


CONFIG = ServerConfig()
