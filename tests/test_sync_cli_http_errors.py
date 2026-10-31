"""Failed requests stop sync and expose only credential-free diagnostics."""

from email.message import Message
from unittest.mock import patch
from urllib.error import HTTPError

import pytest
from test_sync_cli_http import response

from film_iq.movary_http import MovaryHTTPTransport


def test_decoding_failure():
    body = b""
    with (
        patch("film_iq.movary_http.urlopen", return_value=response(200, body)),
        pytest.raises(ValueError, match="Invalid Movary JSON response"),
    ):
        MovaryHTTPTransport("https://movary.invalid", "test-placeholder")("GET", "/movies", None)


def test_http_failure_is_explicit_and_redacted():
    error = HTTPError("https://movary.invalid", 401, "synthetic detail", Message(), None)
    with patch("film_iq.movary_http.urlopen", side_effect=error):
        with pytest.raises(ValueError, match=r"^Movary HTTP status 401$") as caught:
            MovaryHTTPTransport("https://movary.invalid", "test-placeholder")(
                "GET", "/movies", None
            )
        assert caught.value.__suppress_context__
