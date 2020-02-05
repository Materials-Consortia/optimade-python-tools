# pylint: disable=relative-beyond-top-level
import unittest

from optimade.validator import ImplementationValidator

from .utils import get_regular_client, get_index_client


class ServerTestWithValidator(unittest.TestCase):
    def test_with_validator(self):
        validator = ImplementationValidator(client=get_regular_client())
        validator.main()
        self.assertTrue(validator.valid)


class IndexServerTestWithValidator(unittest.TestCase):
    def test_with_validator(self):
        validator = ImplementationValidator(client=get_index_client(), index=True)
        validator.main()
        self.assertTrue(validator.valid)
