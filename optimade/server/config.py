import os
import json
from typing import Any, Optional, Dict, List
from typing_extensions import Literal
from pathlib import Path
from warnings import warn

import json

from pydantic import BaseSettings, root_validator

from optimade import __version__
from optimade.models import Implementation, Provider


class NoFallback(Exception):
    """No fallback value can be found."""


class ServerConfig(BaseSettings):
    """ This class stores server config parameters in a way that
    can be easily extended for new config file types.

    """

    config_file: str = "~/.optimade.json"
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
        index_base_url="http://localhost:5001",
    )
    provider_fields: Dict[Literal["links", "references", "structures"], List[str]] = {
        "structures": ["band_gap", "_mp_chemsys"]
    }
    aliases: Dict[Literal["links", "references", "structures"], Dict[str, str]] = {
        "structures": {
            "id": "task_id",
            "chemical_formula_descriptive": "pretty_formula",
            "chemical_formula_reduced": "pretty_formula",
            "chemical_formula_anonymous": "formula_anonymous",
        }
    }

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
