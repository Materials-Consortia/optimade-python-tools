# pylint: disable=relative-beyond-top-level
import unittest

from optimade.models import LinksResponse

from ..test_server import EndpointTests


class LinksEndpointTests(EndpointTests, unittest.TestCase):
    request_str = "/links"
    response_cls = LinksResponse
