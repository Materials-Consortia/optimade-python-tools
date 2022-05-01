"""Test EntryListingQueryParams middleware"""
import pytest

from optimade.server.exceptions import BadRequest
from optimade.server.middleware import EnsureQueryParamIntegrity


def test_wrong_html_form(check_error_response, both_clients):
    """Using a parameter without equality sign `=` or values should result in a `400 Bad Request` response"""
    from optimade.server.query_params import EntryListingQueryParams

    for valid_query_parameter in EntryListingQueryParams().__dict__:
        request = f"/structures?{valid_query_parameter}"
        with pytest.raises(BadRequest):
            check_error_response(
                request,
                expected_status=400,
                expected_title="Bad Request",
                expected_detail="A query parameter without an equal sign (=) is not supported by this server",
                server=both_clients,
            )


def test_wrong_html_form_one_wrong(check_error_response, both_clients):
    """Using a parameter without equality sign `=` or values should result in a `400 Bad Request` response

    This should hold true, no matter the chosen (valid) parameter separator (either & or ;).
    """
    request = "/structures?filter&include=;response_format=json"
    with pytest.raises(BadRequest):
        check_error_response(
            request,
            expected_status=400,
            expected_title="Bad Request",
            expected_detail="A query parameter without an equal sign (=) is not supported by this server",
            server=both_clients,
        )


def test_parameter_separation(both_clients):
    """No matter the chosen (valid) parameter separator (either & or ;) the parameters should be split correctly"""
    query_part = 'filter=id="mpf_1"&include=;response_format=json'
    expected_result = {'filter=id="mpf_1"', "include=", "response_format=json"}

    parsed_set_of_queries = EnsureQueryParamIntegrity(both_clients.app).check_url(
        query_part
    )
    assert expected_result == parsed_set_of_queries


def test_empty_parameters(both_clients):
    """If parameter separators are present, the middleware should still succeed"""
    query_part = ";;&&;&"
    expected_result = {""}

    parsed_set_of_queries = EnsureQueryParamIntegrity(both_clients.app).check_url(
        query_part
    )
    assert expected_result == parsed_set_of_queries


def test_wrong_query_param(check_error_response):
    request = "/structures?_exmpl_filter=nelements=2"
    check_error_response(
        request,
        expected_status=400,
        expected_title="Bad Request",
        expected_detail="The query parameter(s) '['_exmpl_filter']' are not recognised by this endpoint.",
    )

    request = "/structures?filer=nelements=2"
    check_error_response(
        request,
        expected_status=400,
        expected_title="Bad Request",
        expected_detail="The query parameter(s) '['filer']' are not recognised by this endpoint.",
    )

    request = "/structures/mpf_3819?filter=nelements=2"
    check_error_response(
        request,
        expected_status=400,
        expected_title="Bad Request",
        expected_detail="The query parameter(s) '['filter']' are not recognised by this endpoint.",
    )


def test_handling_prefixed_query_param(check_response):
    request = "/structures?_odbx_filter=nelements=2&filter=elements LENGTH >= 9"
    expected_ids = ["mpf_3819"]
    check_response(request, expected_ids)

    request = (
        "/structures?_unknown_filter=elements HAS 'Si'&filter=elements LENGTH >= 9"
    )
    expected_ids = ["mpf_3819"]
    expected_warnings = [
        {
            "title": "UnknownProviderQueryParameter",
            "detail": "The query parameter(s) '['_unknown_filter']' are unrecognised and have been ignored.",
        }
    ]
    check_response(
        request, expected_ids=expected_ids, expected_warnings=expected_warnings
    )


def test_unsupported_optimade_query_param(check_response):

    request = "/structures?filter=elements LENGTH >= 9&page_number=1"
    expected_ids = ["mpf_3819"]
    expected_warnings = [
        {
            "title": "QueryParamNotUsed",
            "detail": "The query parameter(s) '['page_number']' are not supported by this server and have been ignored.",
        }
    ]
    check_response(
        request, expected_ids=expected_ids, expected_warnings=expected_warnings
    )

    request = "/structures?filter=elements LENGTH >= 9&page_number=1&_unknown_filter=elements HAS 'Si'"
    expected_ids = ["mpf_3819"]
    expected_warnings = [
        {
            "title": "UnknownProviderQueryParameter",
            "detail": "The query parameter(s) '['_unknown_filter']' are unrecognised and have been ignored.",
        },
        {
            "title": "QueryParamNotUsed",
            "detail": "The query parameter(s) '['page_number']' are not supported by this server and have been ignored.",
        },
    ]
    check_response(
        request, expected_ids=expected_ids, expected_warnings=expected_warnings
    )
