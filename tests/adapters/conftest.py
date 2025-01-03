from json import JSONDecodeError
from unittest.mock import Mock

import pytest
import requests


@pytest.fixture(autouse=True)
def set_ci_env(monkeypatch):
    """Super unpleasant workaround to deal with monty's deprecation behaviour."""
    monkeypatch.setenv("CI", "false")
    yield


@pytest.fixture
def mock_requests_get(monkeypatch):
    """Patch requests.get to return the desired mock response."""

    def _mock_requests_get(json_data, status_code=200):
        mock_response = Mock()
        if not isinstance(json_data, dict):

            def mock_raise():
                raise JSONDecodeError(
                    msg="Unable to interpret response as JSON", doc="", pos=0
                )

            mock_response.json = mock_raise
        else:
            mock_response.json.return_value = json_data

        mock_response.status_code = status_code

        def mock_get(*args, **kwargs):
            return mock_response

        monkeypatch.setattr(requests, "get", mock_get)

    return _mock_requests_get
