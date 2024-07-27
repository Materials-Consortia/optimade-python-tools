from unittest.mock import Mock

import pytest
import requests


@pytest.fixture
def mock_requests_get(monkeypatch):
    """Patch requests.get to return the desired mock response."""

    def _mock_requests_get(json_data, status_code=200):
        mock_response = Mock()
        mock_response.json.return_value = json_data
        mock_response.status_code = status_code

        def mock_get(*args, **kwargs):
            return mock_response

        monkeypatch.setattr(requests, "get", mock_get)

    return _mock_requests_get
