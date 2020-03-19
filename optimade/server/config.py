import os
import json
from typing import Any, Optional, Dict, List
from typing_extensions import Literal
from pathlib import Path
from warnings import warn

import json

from pydantic import BaseSettings, Field, root_validator

from optimade import __version__
from optimade.models import Implementation, Provider


class NoFallback(Exception):
    """No fallback value can be found."""


class ServerConfig(BaseSettings):
    """ This class stores server config parameters in a way that
    can be easily extended for new config file types.

    """

    config_file: str = Field(
        "~/.optimade.json", description="File to load alternative defaults from"
    )
    debug: bool = Field(
        False, description="Turns on Debug Mode for the Optimade Server implementation"
    )
    use_real_mongo: bool = Field(
        False, description="Use a real Mongo server rather than MongoMock"
    )
    mongo_database: str = Field(
        "optimade", description="Mongo database for collection data"
    )
    mongo_uri: str = Field("localhost:27017", description="URI for the Mongo server")
    links_collection: str = Field("links", description="Collection name for Links")
    references_collection: str = Field(
        "references", description="Collection name for References"
    )
    structures_collection: str = Field(
        "structures", description="Collection name for Structures"
    )
    page_limit: int = Field(20, description="Default items per page")
    page_limit_max: int = Field(500, description="Max items per page")
    default_db: str = Field("test_server", description="??")
    base_url: Optional[str] = Field(
        None, description="URL for the homepage for this implementation"
    )
    implementation: Implementation = Implementation(
        name="Example implementation",
        version=__version__,
        source_url="https://github.com/Materials-Consortia/optimade-python-tools",
        maintainer=None,
    )
    provider: Provider = Provider(
        prefix="exmpl",
        name="Example provider",
        description="Provider used for examples, not to be assigned to a real database",
        homepage="https://example.com",
        index_base_url="http://localhost:5001",
    )
    provider_fields: Dict[Literal["links", "references", "structures"], List[str]] = {}
    aliases: Dict[Literal["links", "references", "structures"], Dict[str, str]] = {}

    index_links_path: Path = Path(__file__).parent.joinpath("index_links.json")

    @root_validator(pre=True)
    def load_default_settings(cls, values):
        """
        Loads settings from a root file if available and uses that as defaults in
        place of built in defaults
        """
        config_file_path = Path(values.get("config_file", "~/.optimade.json"))

        new_values = {}

        if config_file_path.exists():
            with open(config_file_path) as f:
                new_values = json.load(f)

        new_values.update(values)

        return new_values

    class Config:
        env_prefix = "optimade_"


CONFIG = ServerConfig()
