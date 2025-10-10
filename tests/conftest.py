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
