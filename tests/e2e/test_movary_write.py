"""Contract tests use only an injected transport and synthetic responses."""

import pytest
from conftest import TransportStub

from film_iq.approval import Preview, sync_one
from film_iq.movary_write import MovaryWriteBackend


def test_direct_writes_require_approval() -> None:
    transport = TransportStub()
    backend = MovaryWriteBackend(Preview("Example", 123), "user", transport)
    with pytest.raises(PermissionError):
        backend.add_movie(123)
    with pytest.raises(PermissionError):
        backend.add_watchlist(456)
    with pytest.raises(PermissionError):
        backend._request("POST", backend.watchlist, [], 204)
    assert transport.calls == []


def test_approved_sync_and_retry() -> None:
    transport = TransportStub()
    preview = Preview("Example", 123)
    backend = MovaryWriteBackend(preview, "a/b", transport)
    sync_one(preview, backend)
    with pytest.raises(PermissionError):
        sync_one(preview, backend, execute=True)
    assert transport.calls == []
    assert sync_one(preview, backend, execute=True, approved=True) == "added to watchlist"
    assert sync_one(preview, backend, execute=True, approved=True) == "already on watchlist"
    writes = [(path, body) for method, path, body in transport.calls if method == "POST"]
    assert writes == [
        ("/api/v1/movies/add", {"tmdbId": 123}),
        ("/api/v1/users/a%2Fb/watchlist/movies", [{"movaryId": 456}]),
    ]
