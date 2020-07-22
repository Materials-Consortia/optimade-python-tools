import pytest
import urllib

from optimade.server.exceptions import BadRequest, VersionNotSupported


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


@pytest.mark.parametrize("server", ("regular", "index"))
def test_wrong_html_form(check_error_response, server):
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
                server=server,
            )


@pytest.mark.parametrize("server", ("regular", "index"))
def test_wrong_html_form_one_wrong(check_error_response, server):
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
            server=server,
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


def test_wrong_version(both_clients):
    """If a non-supported versioned base URL is passed, `553 Version Not Supported` should be returned"""
    from optimade.server.config import CONFIG
    from optimade.server.middleware import CheckWronglyVersionedBaseUrls

    version = "/v0"
    url = f"{CONFIG.base_url}{version}/info"

    with pytest.raises(VersionNotSupported):
        CheckWronglyVersionedBaseUrls(both_clients.app).check_url(
            urllib.parse.urlparse(url)
        )


@pytest.mark.parametrize("server", ("regular", "index"))
def test_wrong_version_json_response(check_error_response, server):
    """If a non-supported versioned base URL is passed, `553 Version Not Supported` should be returned

    A specific JSON response should also occur.
    """
    from optimade.server.config import CONFIG
    from optimade.server.routers.utils import BASE_URL_PREFIXES

    version = "/v0"
    request = f"{version}/info"
    with pytest.raises(VersionNotSupported):
        check_error_response(
            request,
            expected_status=553,
            expected_title="Version Not Supported",
            expected_detail=(
                f"The parsed versioned base URL {version!r} from '{CONFIG.base_url}{request}' is not supported by this implementation. "
                f"Supported versioned base URLs are: {', '.join(BASE_URL_PREFIXES.values())}"
            ),
            server=server,
        )


def test_multiple_versions_in_path(both_clients):
    """If another version is buried in the URL path, only the OPTIMADE versioned URL path part should be recognized."""
    from optimade.server.config import CONFIG
    from optimade.server.middleware import CheckWronglyVersionedBaseUrls
    from optimade.server.routers.utils import BASE_URL_PREFIXES

    non_valid_version = "/v0.5"
    org_base_url = CONFIG.base_url

    try:
        CONFIG.base_url = f"https://example.org{non_valid_version}/my_database/optimade"

        for valid_version_prefix in BASE_URL_PREFIXES.values():
            url = f"{CONFIG.base_url}{valid_version_prefix}/info"
            CheckWronglyVersionedBaseUrls(both_clients.app).check_url(
                urllib.parse.urlparse(url)
            )

        # Test also that the a non-valid OPTIMADE version raises
        url = f"{CONFIG.base_url}/v0/info"
        with pytest.raises(VersionNotSupported):
            CheckWronglyVersionedBaseUrls(both_clients.app).check_url(
                urllib.parse.urlparse(url)
            )
    finally:
        if org_base_url:
            CONFIG.base_url = org_base_url
