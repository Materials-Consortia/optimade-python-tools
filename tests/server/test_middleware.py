import pytest

from optimade.server.exceptions import BadRequest


def test_regular_CORS_request(both_clients):
    response = both_clients.get("/info", headers={"Origin": "http://example.org"})
    assert ("access-control-allow-origin", "*") in tuple(
        response.headers.items()
    ), f"Access-Control-Allow-Origin header not found in response headers: {response.headers}"


def test_preflight_CORS_request(both_clients):
    headers = {
        "Origin": "http://example.org",
        "Access-Control-Request-Method": "GET",
    }
    response = both_clients.options("/info", headers=headers)
    for response_header in (
        "Access-Control-Allow-Origin",
        "Access-Control-Allow-Methods",
    ):
        assert response_header.lower() in list(
            response.headers.keys()
        ), f"{response_header} header not found in response headers: {response.headers}"


def test_wrong_html_form(check_error_response):
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
            )


def test_wrong_html_form_one_wrong(check_error_response):
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
        )


def test_parameter_separation(both_clients):
    """No matter the chosen (valid) parameter separator (either & or ;) the parameters should be split correctly"""
    from optimade.server.middleware import EnsureQueryParamIntegrity

    query_part = 'filter=id="mpf_1"&include=;response_format=json'
    expected_result = {'filter=id="mpf_1"', "include=", "response_format=json"}

    parsed_set_of_queries = EnsureQueryParamIntegrity(both_clients.app).check_url(
        query_part
    )
    assert expected_result == parsed_set_of_queries


def test_empty_parameters(both_clients):
    """If parameter separators are present, the middleware should still succeed"""
    from optimade.server.middleware import EnsureQueryParamIntegrity

    query_part = ";;&&;&"
    expected_result = {""}

    parsed_set_of_queries = EnsureQueryParamIntegrity(both_clients.app).check_url(
        query_part
    )
    assert expected_result == parsed_set_of_queries
