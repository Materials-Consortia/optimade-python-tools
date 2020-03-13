# pylint: disable=protected-access,pointless-statement,relative-beyond-top-level
import os
import unittest

from pathlib import Path

from optimade.server.config import ServerConfig, CONFIG

from .utils import SetClient



class TestDebugOff(SetClient, unittest.TestCase):

    server = "regular"

    def test_env_variable(self):
        """Set OPTIMADE_DEBUG environment variable and check CONFIG picks up on it correctly"""
        os.environ["OPTIMADE_DEBUG"] = "true"
        CONFIG = ServerConfig()
        self.assertTrue(CONFIG.debug)

        os.environ.pop("OPTIMADE_DEBUG", None)
        CONFIG = ServerConfig()
        self.assertFalse(CONFIG.debug)

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
