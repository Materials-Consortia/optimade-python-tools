# pylint: disable=relative-beyond-top-level,import-outside-toplevel
import os
import unittest
from traceback import print_exc

from optimade import __api_version__
from optimade.validator import ImplementationValidator

from .utils import SetClient


class ServerTestWithValidator(SetClient, unittest.TestCase):

    server = "regular"

    def test_with_validator(self):
        validator = ImplementationValidator(client=self.client)
        try:
            validator.main()
        except Exception:
            print_exc()
        self.assertTrue(validator.valid)


class IndexServerTestWithValidator(SetClient, unittest.TestCase):

    server = "index"

    def test_with_validator(self):
        validator = ImplementationValidator(client=self.client, index=True)
        try:
            validator.main()
        except Exception:
            print_exc()
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
            "The environment variable OPTIMADE_CI_FORCE_MONGO cannot be parsed as an int."
        )


class AsTypeTestsWithValidator(SetClient, unittest.TestCase):

    server = "regular"

    def test_as_type_with_validator(self):

        base_url = f"http://example.org/v{__api_version__.split('.')[0]}"
        test_urls = {
            f"{base_url}/structures": "structures",
            f"{base_url}/structures/mpf_1": "structure",
            f"{base_url}/references": "references",
            f"{base_url}/references/dijkstra1968": "reference",
            f"{base_url}/info": "info",
            f"{base_url}/links": "links",
        }
        with unittest.mock.patch(
            "requests.get", unittest.mock.Mock(side_effect=self.client.get)
        ):
            for url, as_type in test_urls.items():
                validator = ImplementationValidator(
                    base_url=url, as_type=as_type, verbosity=5
                )
                try:
                    validator.main()
                except Exception:
                    print_exc()
                self.assertTrue(validator.valid)
