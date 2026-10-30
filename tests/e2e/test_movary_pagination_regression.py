"""Pinned Movary pagination edge cases, using synthetic responses only."""

import pytest

from film_iq.approval import Preview, sync_one
from film_iq.movary_write import MovaryWriteBackend


def test_short_nonfinal_watchlist_page_never_posts() -> None:
    calls: list[str] = []

    def transport(method: str, path: str, body: object) -> tuple[int, object]:
        calls.append(method)
        if "search" in path:
            return 200, {
                "results": [{"ids": {"tmdb": 123, "movary": 456}}],
                "currentPage": 1,
                "maxPage": 1,
            }
        return 200, {
            "watchlist": [{"movie": {"ids": {"movary": 99}}}],
            "currentPage": 1,
            "maxPage": 2,
        }

    preview = Preview("Example", 123)
    with pytest.raises(ValueError, match="Incomplete"):
        sync_one(
            preview, MovaryWriteBackend(preview, "user", transport), execute=True, approved=True
        )
    assert calls == ["GET", "GET"]
