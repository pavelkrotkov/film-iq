"""Failed requests stop sync and expose only credential-free diagnostics."""

from email.message import Message
from unittest.mock import patch
from urllib.error import HTTPError, URLError

import pytest
from test_sync_cli_http import response

from film_iq.movary_http import MovaryHTTPTransport


@pytest.mark.parametrize("body", [b"", b"not json", b"\xff"])
def test_decoding_failure(body):
    with (
        patch("film_iq.movary_http.urlopen", return_value=response(200, body)),
        pytest.raises(ValueError, match="Invalid Movary JSON response"),
    ):
        MovaryHTTPTransport("https://movary.invalid", "test-placeholder")("GET", "/movies", None)


@pytest.mark.parametrize(
    "error",
    [URLError("synthetic detail"), TimeoutError("synthetic detail"), OSError("synthetic detail")],
)
def test_transport_failure_is_explicit_and_redacted(error):
    with patch("film_iq.movary_http.urlopen", side_effect=error):
        with pytest.raises(ValueError, match=r"^Movary HTTP transport failed$") as caught:
            MovaryHTTPTransport("https://movary.invalid", "test-placeholder")(
                "GET", "/movies", None
            )
        assert caught.value.__suppress_context__


def test_http_failure_is_explicit_and_redacted():
    error = HTTPError("https://movary.invalid", 401, "synthetic detail", Message(), None)
    with patch("film_iq.movary_http.urlopen", side_effect=error):
        with pytest.raises(ValueError, match=r"^Movary HTTP status 401$") as caught:
            MovaryHTTPTransport("https://movary.invalid", "test-placeholder")(
                "GET", "/movies", None
            )
        assert caught.value.__suppress_context__


def test_returned_failure_status_is_not_absence():
    with (
        patch("film_iq.movary_http.urlopen", return_value=response(503, b"")),
        pytest.raises(ValueError, match="Movary HTTP status 503"),
    ):
        MovaryHTTPTransport("https://movary.invalid", "test-placeholder")("GET", "/movies", None)
