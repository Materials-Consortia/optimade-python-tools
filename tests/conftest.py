import os
from pathlib import Path


def pytest_configure(config):
    """
    Method that runs before pytest collects tests so no modules
    are imported
    """
    cwd = Path(__file__).parent
    os.environ["OPTIMADE_CONFIG_FILE"] = str(cwd / "test_config.json")
