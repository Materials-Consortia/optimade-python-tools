import numpy
from pydantic import AnyUrl
from pydantic.tools import parse_obj_as
from datetime import datetime
from optimade.adapters.hdf5 import (
    generate_hdf5_file_content,
    generate_response_from_hdf5,
)
from fastapi.encoders import jsonable_encoder
from optimade.models.jsonapi import Response
from optimade.server.config import CONFIG


def test_response_format(check_response):
    request = (
        '/structures?filter=chemical_formula_descriptive="Ac"&response_format=json'
    )
    expected_ids = ["mpf_1"]
    check_response(request, expected_ids)

    if "hdf5" in CONFIG.enabled_response_formats:
        request = (
            '/structures?filter=chemical_formula_descriptive="Ac"&response_format=hdf5'
        )
        check_response(request, expected_ids)


if "hdf5" in CONFIG.enabled_response_formats:

    def test_single_entry(check_response):
        """For single entry. Default value for `include` is 'references'"""
        request = "/structures/mpf_1?response_format=hdf5"
        expected_ids = "mpf_1"
        check_response(request, expected_ids)

    def test_convert_to_hdf5_and_back():
        test_dict = {
            "int": 1,
            "float": 5.26,
            "string": "str",
            "datetime": datetime.now(),
            "list": [[[2.3, 6.3], [8.6, 4.5]], [[8.9, 9.4], [5.6, 3.5]]],
            "dict": {"a key": "a value", "another key": 7.33},
            "tuple": (95, 63),
            "bool": False,
            "AnyUrl": parse_obj_as(AnyUrl, "https://example.com"),
            "None": None,
            "empty": [],
            "numpy_int64": numpy.int64(42),
            "numpy_float32": numpy.float32(0.88153),
            "numpy_bool": numpy.bool_(True),
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


def test_unsupported_response_format(check_error_response):
    request = '/structures?filter=chemical_formula_descriptive="Ac"&response_format=png'
    error_detail = f"Response format png is not supported, please use one of the supported response_formats: {','.join(CONFIG.get_enabled_response_formats())}"
    check_error_response(
        request,
        expected_status=400,
        expected_title="Bad Request",
        expected_detail=error_detail,
    )
