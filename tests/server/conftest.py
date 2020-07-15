import pytest

from optimade.server.config import CONFIG


@pytest.fixture(scope="session")
def client():
    """Return TestClient for the regular OPTIMADE server"""
    from .utils import client_factory

    return client_factory()(server="regular")


@pytest.fixture(scope="session")
def index_client():
    """Return TestClient for the index OPTIMADE server"""
    from .utils import client_factory

    return client_factory()(server="index")


@pytest.fixture(scope="session", params=["regular", "index"])
def both_clients(request):
    """Return TestClient for both the regular and index OPTIMADE server"""
    from .utils import client_factory

    return client_factory()(server=request.param)


@pytest.fixture
def get_good_response(client, index_client):
    """Get response with some sanity checks, expecting '200 OK'"""

    def inner(request: str, server: str = "regular") -> dict:
        if server == "regular":
            used_client = client
        elif server == "index":
            used_client = index_client
        else:
            pytest.fail(
                f"Wrong value for 'server': {server}. It must be either 'regular' or 'index'."
            )

        try:
            response = used_client.get(request)
            assert response.status_code == 200, f"Request failed: {response.json()}"
            response = response.json()
        except Exception as exc:
            print("Request attempted:")
            print(f"{used_client.base_url}{used_client.version}{request}")
            raise exc
        else:
            return response

    return inner


@pytest.fixture
def check_response(get_good_response):
    """Fixture to check "good" response"""
    from typing import List

    def inner(
        request: str,
        expected_ids: List[str],
        page_limit: int = CONFIG.page_limit,
        expected_return: int = None,
        expected_as_is: bool = False,
        server: str = "regular",
    ):
        response = get_good_response(request, server)

        response_ids = [struct["id"] for struct in response["data"]]

        if expected_return is None:
            expected_return = len(expected_ids)

        assert response["meta"]["data_returned"] == expected_return

        if not expected_as_is:
            expected_ids = sorted(expected_ids)

        if len(expected_ids) > page_limit:
            assert expected_ids[:page_limit] == response_ids
        else:
            assert expected_ids == response_ids

    return inner


@pytest.fixture
def check_error_response(client, index_client):
    """General method for testing expected erroneous response"""

    def inner(
        request: str,
        expected_status: int = None,
        expected_title: str = None,
        expected_detail: str = None,
        server: str = "regular",
    ):
        response = None
        if server == "regular":
            used_client = client
        elif server == "index":
            used_client = index_client
        else:
            pytest.fail(
                f"Wrong value for 'server': {server}. It must be either 'regular' or 'index'."
            )

        try:
            response = used_client.get(request)
            assert response.status_code == expected_status, (
                f"Request should have been an error with status code {expected_status}, "
                f"but instead {response.status_code} was received.\nResponse:\n{response.json()}",
            )

            response = response.json()
            assert len(response["errors"]) == 1, response.get(
                "errors", "'errors' not found in response"
            )
            assert response["meta"]["data_returned"] == 0, response.get(
                "meta", "'meta' not found in response"
            )

            error = response["errors"][0]
            assert str(expected_status) == error["status"], error
            assert expected_title == error["title"], error

            if expected_detail is None:
                expected_detail = "Error trying to process rule "
                assert error["detail"].startswith(expected_detail), (
                    "No expected_detail provided and the error did not start with a standard Lark "
                    "error message."
                )
            else:
                assert expected_detail == error["detail"], error

        except Exception:
            print("Request attempted:")
            print(f"{used_client.base_url}{used_client.version}{request}")
            if response:
                print(f"\nCaptured response:\n{response}")
            raise

    return inner
