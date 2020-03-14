# pylint: disable=relative-beyond-top-level,import-outside-toplevel
import os
import unittest

from optimade.validator import ImplementationValidator

from .utils import SetClient
from ..test_setup import setup_config

setup_config()


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


def test_mongo_backend_package_used():
    import pymongo
    import mongomock
    from optimade.server.entry_collections import client

    force_mongo_env_var = os.environ.get("OPTIMADE_CI_FORCE_MONGO", None)
    if force_mongo_env_var is None:
        return

    if int(force_mongo_env_var) == 1:
        assert issubclass(client.__class__, pymongo.MongoClient)
    elif int(force_mongo_env_var) == 0:
        assert issubclass(client.__class__, mongomock.MongoClient)
    else:
        raise Exception(
            f"The environment variable OPTIMADE_CI_FORCE_MONGO cannot be parsed as an int."
        )
