# pylint: disable=relative-beyond-top-level
import unittest

from optimade.validator import ImplementationValidator

from .utils import SetClient


class ServerTestWithValidator(SetClient, unittest.TestCase):

    server = "regular"

    def test_with_validator(self):
        validator = ImplementationValidator(client=self.client)
        validator.main()
        self.assertTrue(validator.valid)


class IndexServerTestWithValidator(SetClient, unittest.TestCase):

    server = "index"

    def test_with_validator(self):
        validator = ImplementationValidator(client=self.client, index=True)
        validator.main()
        self.assertTrue(validator.valid)
