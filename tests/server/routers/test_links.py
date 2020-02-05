# pylint: disable=relative-beyond-top-level
import unittest

from optimade.models import LinksResponse

from ..utils import EndpointTestsMixin


class LinksEndpointTests(EndpointTestsMixin, unittest.TestCase):

    request_str = "/links"
    response_cls = LinksResponse


class IndexLinksEndpointTests(EndpointTestsMixin, unittest.TestCase):

    server = "index"
    request_str = "/links"
    response_cls = LinksResponse
