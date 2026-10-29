"""HTTP behavior with mocked urlopen only; no live calls or real credentials."""

import json
from unittest.mock import MagicMock, patch

import pytest

from film_iq.movary_http import MovaryHTTPTransport


def response(status, body):
    result = MagicMock()
    result.__enter__.return_value = result
    result.status = status
    result.read.return_value = body
    return result


def test_request_json_headers_and_timeout():
    with patch(
        "film_iq.movary_http.urlopen", return_value=response(200, b'{"movaryId":456}')
    ) as opening:
        transport = MovaryHTTPTransport("https://movary.invalid/", "test-placeholder")
        assert transport("GET", "/api/v1/movies/search", None) == (200, {"movaryId": 456})
        request = opening.call_args.args[0]
        assert request.full_url == "https://movary.invalid/api/v1/movies/search"
        assert request.method == "GET"
        assert request.get_header("Authorization") == "Bearer test-placeholder"
        assert request.get_header("Accept") == "application/json"
        assert opening.call_args.kwargs == {"timeout": 30}


@pytest.mark.parametrize("body", [None, {"tmdbId": 123}])
def test_request_body(body):
    """Encode JSON only when a request has a body, including its content type."""
    with patch("film_iq.movary_http.urlopen", return_value=response(204, b"")) as opening:
        transport = MovaryHTTPTransport("https://movary.invalid", "test-placeholder")
        assert transport("POST", "/movies", body) == (204, None)
        request = opening.call_args.args[0]
        assert request.data == (None if body is None else json.dumps(body).encode())
        assert request.has_header("Content-type") == (body is not None)
