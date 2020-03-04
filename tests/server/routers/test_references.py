# pylint: disable=relative-beyond-top-level
import unittest

from optimade.models import ReferenceResponseMany, ReferenceResponseOne

from ..utils import EndpointTestsMixin


class ReferencesEndpointTests(EndpointTestsMixin, unittest.TestCase):

    request_str = "/references"
    response_cls = ReferenceResponseMany


class SingleReferenceEndpointTests(EndpointTestsMixin, unittest.TestCase):

    test_id = "dijkstra1968"
    request_str = f"/references/{test_id}"
    response_cls = ReferenceResponseOne


class SingleReferenceEndpointTestsDifficult(EndpointTestsMixin, unittest.TestCase):

    test_id = "dummy/20.19"
    request_str = f"/references/{test_id}"
    response_cls = ReferenceResponseOne
