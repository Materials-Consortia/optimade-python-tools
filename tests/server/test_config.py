# pylint: disable=protected-access,pointless-statement,relative-beyond-top-level
import os
import unittest

from pathlib import Path

from optimade.server.config import ServerConfig, CONFIG

from .utils import SetClient


class LoadFromIniTest(unittest.TestCase):
    """Test server.config.ServerConfig.load_from_ini"""

    def test_config_ini(self):
        """Invoke CONFIG using config_test.ini"""
        CONFIG = ServerConfig(
            server_cfg=Path(__file__).parent.joinpath("server_test_ini.cfg").resolve()
        )

        CONFIG.default_db  # Initiate CONFIG, running load_from_json()
        # _path should now be updated with the correct path to the config json file:
        self.assertEqual(
            CONFIG._path, Path(__file__).parent.joinpath("config_test.ini").resolve()
        )


class LoadFromJsonTest(unittest.TestCase):
    """Test server.config.ServerConfig.load_from_json"""

    def test_config_json(self):
        """Invoke CONFIG using config_test.json"""
        CONFIG = ServerConfig(
            server_cfg=Path(__file__).parent.joinpath("server_test_json.cfg").resolve()
        )

        CONFIG.default_db  # Initiate CONFIG, running load_from_json()
        # _path should now be updated with the correct path to the config json file:
        self.assertEqual(
            CONFIG._path, Path(__file__).parent.joinpath("config_test.json").resolve()
        )


class TestDebug(unittest.TestCase):
    """Test if debug mode is correctly set and respected"""

    def test_env_variable(self):
        """Set OPTIMADE_DEBUG environment variable and check CONFIG picks up on it correctly"""
        os.environ["OPTIMADE_DEBUG"] = "1"
        CONFIG = ServerConfig()
        self.assertTrue(CONFIG.debug)

        os.environ.pop("OPTIMADE_DEBUG", None)
        CONFIG = ServerConfig()
        self.assertFalse(CONFIG.debug)


class TestDebugOff(SetClient, unittest.TestCase):

    server = "regular"

    def test_debug_is_respected_when_off(self):
        """Make sure traceback is toggleable according to debug mode - here OFF

        TODO: This should be moved to a separate test file that tests the exception handlers.
        """
        if CONFIG.debug:
            CONFIG.debug = False

        response = self.client.get("/non/existent/path")
        self.assertEqual(
            response.status_code,
            404,
            msg=f"Request should have failed, but didn't: {response.json()}",
        )

        response = response.json()
        self.assertNotIn("data", response)
        self.assertIn("meta", response)

        self.assertNotIn(f"{CONFIG.provider.prefix}traceback", response["meta"])


class IndexTestDebugOff(SetClient, unittest.TestCase):

    server = "index"

    def test_debug_is_respected_when_off(self):
        """Make sure traceback is toggleable according to debug mode - here OFF

        TODO: This should be moved to a separate test file that tests the exception handlers.
        """
        if CONFIG.debug:
            CONFIG.debug = False

        response = self.client.get("/non/existent/path")
        self.assertEqual(
            response.status_code,
            404,
            msg=f"Request should have failed, but didn't: {response.json()}",
        )

        response = response.json()
        self.assertNotIn("data", response)
        self.assertIn("meta", response)

        self.assertNotIn(f"{CONFIG.provider.prefix}traceback", response["meta"])


class TestDebugOn(SetClient, unittest.TestCase):

    server = "regular"

    def test_debug_is_respected_when_off(self):
        """Make sure traceback is toggleable according to debug mode - here OFF

        TODO: This should be moved to a separate test file that tests the exception handlers.
        """
        CONFIG.debug = True

        response = self.client.get("/non/existent/path")
        self.assertEqual(
            response.status_code,
            404,
            msg=f"Request should have failed, but didn't: {response.json()}",
        )

        response = response.json()
        self.assertNotIn("data", response)
        self.assertIn("meta", response)

        self.assertIn(f"{CONFIG.provider.prefix}traceback", response["meta"])


class IndexTestDebugOn(SetClient, unittest.TestCase):

    server = "index"

    def test_debug_is_respected_when_off(self):
        """Make sure traceback is toggleable according to debug mode - here OFF

        TODO: This should be moved to a separate test file that tests the exception handlers.
        """
        CONFIG.debug = True

        response = self.client.get("/non/existent/path")
        self.assertEqual(
            response.status_code,
            404,
            msg=f"Request should have failed, but didn't: {response.json()}",
        )

        response = response.json()
        self.assertNotIn("data", response)
        self.assertIn("meta", response)

        self.assertIn(f"{CONFIG.provider.prefix}traceback", response["meta"])
