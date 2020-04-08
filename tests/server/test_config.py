# pylint: disable=protected-access,pointless-statement,relative-beyond-top-level
import json
import os
import unittest

from pathlib import Path

from optimade.server.config import ServerConfig, CONFIG

from .utils import SetClient


class ConfigTests(unittest.TestCase):
    def test_env_variable(self):
        """Set OPTIMADE_DEBUG environment variable and check CONFIG picks up on it correctly"""
        os.environ["OPTIMADE_DEBUG"] = "true"
        CONFIG = ServerConfig()
        self.assertTrue(CONFIG.debug)

        os.environ.pop("OPTIMADE_DEBUG", None)
        CONFIG = ServerConfig()
        self.assertFalse(CONFIG.debug)

    def test_default_config_path(self):
        """Make sure the default config path works
        Expected default config path: PATH/TO/USER/HOMEDIR/.optimade.json
        """
        # Reset OPTIMADE_CONFIG_FILE
        original_OPTIMADE_CONFIG_FILE = os.environ.get("OPTIMADE_CONFIG_FILE", "")
        os.environ.pop("OPTIMADE_CONFIG_FILE")

        with open(
            Path(__file__).parent.parent.joinpath("test_config.json"), "r"
        ) as config_file:
            config = json.load(config_file)

        different_base_url = "http://something_you_will_never_think_of.com"
        config["base_url"] = different_base_url

        # Try-finally to make sure we don't overwrite possible existing `.optimade.json`
        original = Path.home().joinpath(".optimade.json")
        restore = False
        if original.exists():
            restore = True
            with open(original, "rb") as original_file:
                original_file_content = original_file.read()
        try:
            with open(
                Path.home().joinpath(".optimade.json"), "w"
            ) as default_config_file:
                json.dump(config, default_config_file)
            CONFIG = ServerConfig()
            self.assertEqual(
                CONFIG.base_url,
                different_base_url,
                f"\nDumped file content:\n{config}.\n\nLoaded CONFIG:\n{CONFIG}",
            )
        finally:
            if restore:
                with open(original, "wb") as original_file:
                    original_file.write(original_file_content)

        # Restore OPTIMADE_CONFIG_FILE
        os.environ["OPTIMADE_CONFIG_FILE"] = original_OPTIMADE_CONFIG_FILE


class TestRegularServerConfig(SetClient, unittest.TestCase):

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

        self.assertNotIn(f"_{CONFIG.provider.prefix}_traceback", response["meta"])

    def test_debug_is_respected_when_on(self):
        """Make sure traceback is toggleable according to debug mode - here ON

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

        self.assertIn(f"_{CONFIG.provider.prefix}_traceback", response["meta"])


class TestRegularIndexServerConfig(SetClient, unittest.TestCase):

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

        self.assertNotIn(f"_{CONFIG.provider.prefix}_traceback", response["meta"])

    def test_debug_is_respected_when_on(self):
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

        self.assertIn(f"_{CONFIG.provider.prefix}_traceback", response["meta"])
