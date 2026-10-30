"""Original failure evidence survives without copying payloads or error messages."""

import hashlib
from urllib.error import URLError

import pytest
from test_availability_research import FILM, observe


@pytest.mark.parametrize(
    "body,phase,error_type",
    [
        (b"{", "json_decode", "JSONDecodeError"),
        (b'{"id":123,"results":{}}', "schema", "KeyError"),
    ],
)
def test_successful_http_failure_preserves_original_hash(monkeypatch, body, phase, error_type):
    monkeypatch.setenv("TMDB_READ_ACCESS_TOKEN", "fictional-secret")
    result = observe(FILM, "tmdb", True, lambda request: (200, body, {}))
    assert result["state"] == "unknown" and "offers" not in result
    assert result["response_sha256"] == hashlib.sha256(body).hexdigest()
    assert result["failure"] == {"phase": phase, "type": error_type}
    assert "fictional-secret" not in repr(result)


def test_transport_failure_preserves_cause_without_sensitive_message(monkeypatch):
    monkeypatch.setenv("TMDB_READ_ACCESS_TOKEN", "fictional-secret")

    def failed(request):
        raise URLError("https://example.org?api_key=fictional-secret")

    result = observe(FILM, "tmdb", True, failed)
    assert result["failure"] == {"phase": "transport", "type": "URLError"}
    assert "response_sha256" not in result and "offers" not in result
    assert "fictional-secret" not in repr(result)
