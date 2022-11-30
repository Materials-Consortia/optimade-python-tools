import os
from pathlib import Path

import pytest


def pytest_configure(config):
    """Method that runs before pytest collects tests so no modules are imported"""
    cwd = Path(__file__).parent
    os.environ["OPTIMADE_CONFIG_FILE"] = str(cwd / "test_config.json")


@pytest.fixture(scope="session")
def top_dir() -> Path:
    """Return Path instance for the repository's top (root) directory"""
    return Path(__file__).parent.parent.resolve()


@pytest.fixture(scope="module")
def mapper():
    """Mapper-factory to import a mapper from optimade.server.mappers"""
    from optimade.server import mappers

    def _mapper(name: str) -> mappers.BaseResourceMapper:  # type: ignore[return]
        """Return named resource mapper"""
        try:
            res = getattr(mappers, name)
        except AttributeError:
            pytest.fail(f"Could not retrieve {name!r} from optimade.server.mappers.")
        else:
            return res

    return _mapper
