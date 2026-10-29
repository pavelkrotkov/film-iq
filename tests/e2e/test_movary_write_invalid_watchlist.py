"""Incomplete or malformed watchlist reads cannot authorize a write."""

import pytest

from film_iq.approval import Preview, sync_one
from film_iq.movary_write import MovaryWriteBackend


@pytest.mark.parametrize(
    ("second_page", "error"),
    [
        (
            {"watchlist": [{"movie": {"ids": {"movary": 99}}}], "currentPage": 1, "maxPage": 2},
            "Inconsistent",
        ),
        (
            {"watchlist": [{"movie": {"ids": {"movary": 99}}}], "currentPage": 2, "maxPage": 3},
            "Inconsistent",
        ),
        ({"watchlist": [], "currentPage": 2, "maxPage": 2}, "Incomplete"),
    ],
)
def test_invalid_later_page_never_posts(second_page: dict, error: str) -> None:
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
                "watchlist": [{"movie": {"ids": {"movary": 99}}}] * 100,
                "currentPage": 1,
                "maxPage": 2,
            }
        return 200, second_page

    preview = Preview("Example", 123)
    with pytest.raises(ValueError, match=error):
        sync_one(
            preview, MovaryWriteBackend(preview, "user", transport), execute=True, approved=True
        )
    assert calls == ["GET", "GET", "GET"]


@pytest.mark.parametrize("movie_id", [None, True, 0, -1, "456"])
def test_invalid_watchlist_id_never_posts(movie_id: object) -> None:
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
            "watchlist": [{"movie": {"ids": {"movary": movie_id}}}],
            "currentPage": 1,
            "maxPage": 1,
        }

    preview = Preview("Example", 123)
    with pytest.raises(ValueError, match="Invalid Movary or TMDB ID"):
        sync_one(
            preview, MovaryWriteBackend(preview, "user", transport), execute=True, approved=True
        )
    assert calls == ["GET", "GET"]
