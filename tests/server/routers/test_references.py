# pylint: disable=relative-beyond-top-level
import unittest

from optimade.models import ReferenceResponseMany, ReferenceResponseOne

from ..test_server import EndpointTests


class ReferencesEndpointTests(EndpointTests, unittest.TestCase):
    request_str = "/references"
    response_cls = ReferenceResponseMany


class SingleReferenceEndpointTests(EndpointTests, unittest.TestCase):
    test_id = "dijkstra1968"
    request_str = f"/references/{test_id}"
    response_cls = ReferenceResponseOne
