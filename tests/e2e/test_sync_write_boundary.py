"""Synthetic integration seam; the real adapters and API are not connected yet."""

import pytest
from stub_backend import StubBackend

from film_iq.approval import Preview, sync_one


def test_write_boundary_preview_approval_and_retry() -> None:
    backend = StubBackend()
    preview = Preview("Example", 123)
    assert sync_one(preview, backend) == "Preview: add Example (TMDB 123) to watchlist"
    with pytest.raises(PermissionError):
        sync_one(preview, backend, execute=True)
    assert backend.writes == []
    assert sync_one(preview, backend, execute=True, approved=True) == "added to watchlist"
    assert sync_one(preview, backend, execute=True, approved=True) == "already on watchlist"
    assert backend.writes == [("movie", 123), ("watchlist", 456)]
    assert backend.watchlist == {99, 456}
