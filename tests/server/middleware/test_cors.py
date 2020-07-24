"""Test CORS middleware"""


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
