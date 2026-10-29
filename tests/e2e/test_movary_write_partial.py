"""A failed later watchlist page must never imply absence."""

import pytest

from film_iq.approval import Preview, sync_one
from film_iq.movary_write import MovaryWriteBackend


def test_partial_watchlist_does_not_write() -> None:
    calls: list[str] = []

    def transport(method: str, path: str, body: object) -> tuple[int, object]:
        calls.append(method)
        if "search" in path:
            return 200, {
                "results": [{"ids": {"tmdb": 123, "movary": 456}}],
                "currentPage": 1,
                "maxPage": 1,
            }
        if "page=1" in path:
            return 200, {
                "watchlist": [{"movie": {"ids": {"movary": 99}}}],
                "currentPage": 1,
                "maxPage": 2,
            }
        return 500, {}

    preview = Preview("Example", 123)
    with pytest.raises(ValueError, match="HTTP status"):
        sync_one(
            preview, MovaryWriteBackend(preview, "user", transport), execute=True, approved=True
        )
    assert calls == ["GET", "GET", "GET"]
