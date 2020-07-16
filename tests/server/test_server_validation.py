import os
from traceback import print_exc

from optimade.validator import ImplementationValidator


def test_with_validator(both_clients):
    from optimade.server.main_index import app

    validator = ImplementationValidator(
        client=both_clients, index=both_clients.app == app,
    )
    try:
        validator.main()
    except Exception:
        print_exc()
    assert validator.valid


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


def test_as_type_with_validator(client):
    import unittest

    test_urls = {
        f"{client.base_url}structures": "structures",
        f"{client.base_url}structures/mpf_1": "structure",
        f"{client.base_url}references": "references",
        f"{client.base_url}references/dijkstra1968": "reference",
        f"{client.base_url}info": "info",
        f"{client.base_url}links": "links",
    }
    with unittest.mock.patch(
        "requests.get", unittest.mock.Mock(side_effect=client.get)
    ):
        for url, as_type in test_urls.items():
            validator = ImplementationValidator(
                base_url=url, as_type=as_type, verbosity=5
            )
            try:
                validator.main()
            except Exception:
                print_exc()
            assert validator.valid
