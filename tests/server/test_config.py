# pylint: disable=import-outside-toplevel,protected-access,pointless-statement
import unittest

from pathlib import Path


class LoadFromJsonTest(unittest.TestCase):
    """Test server.config.ServerConfig.load_from_json"""

    def test_config_json(self):
        """Invoke CONFIG using config.json"""
        from optimade.server.config import ServerConfig

        CONFIG = ServerConfig(
            server_cfg=Path(__file__).parent.joinpath("server_test.cfg").resolve()
        )

        CONFIG.default_db  # Initiate CONFIG, running load_from_json()
        # _path should now be updated with the correct path to the config json file:
        self.assertEqual(
            CONFIG._path, Path(__file__).parent.joinpath("config_test.json").resolve()
        )
