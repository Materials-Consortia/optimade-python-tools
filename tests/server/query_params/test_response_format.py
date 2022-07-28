import numpy
from pydantic import AnyUrl
from pydantic.tools import parse_obj_as
from datetime import datetime
from optimade.models import ReferenceResponseOne
from tests.server.utils import RegularEndpointTests
from optimade.adapters.hdf5 import (
    generate_hdf5_file_content,
    generate_response_from_hdf5,
)
from fastapi.encoders import jsonable_encoder
from optimade.models.jsonapi import Response


def test_response_format(check_response):
    request = '/structures?filter=_exmpl_chemsys="Ac"&response_format=json'
    expected_ids = ["mpf_1"]
    check_response(request, expected_ids)

    request = '/structures?filter=_exmpl_chemsys="Ac"&response_format=hdf5'
    check_response(request, expected_ids)


class TestSingleReferenceEndpoint(RegularEndpointTests):
    test_id = "dijkstra1968"
    request_str = f"/references/{test_id}&response_format=hdf5"
    response_cls = ReferenceResponseOne


def test_convert_to_hdf5_and_back():
    test_dict = {
        "int": 1,
        "float": 5.26,
        "string": "str",
        "datetime": datetime.now(),
        "list": [[2.3, 4.5], [8.9, 5.6]],
        "dict": {"a key": "a value", "another key": 7.33},
        "tuple": (95, 63),
        "bool": False,
        "AnyUrl": parse_obj_as(AnyUrl, "https://example.com"),
        "None": None,
        "empty": [],
        "numpy_int64": numpy.int64(42),
        "numpy_float32": numpy.float32(0.88153),
        "numpy_bool": numpy.bool(True),
        "numpy_array": numpy.array([(1, 2), (3, 4)]),
    }

    hdf5_file_content = generate_hdf5_file_content(test_dict)

    returned_dict = generate_response_from_hdf5(hdf5_file_content)
    reference_dict = jsonable_encoder(
        test_dict, custom_encoder=Response.Config.json_encoders
    )
    returned_dict = jsonable_encoder(
        returned_dict, custom_encoder=Response.Config.json_encoders
    )
    assert reference_dict == returned_dict
