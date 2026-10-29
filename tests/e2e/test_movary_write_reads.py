"""Reject incomplete search and watchlist reads before writing."""

from urllib.parse import parse_qs, urlsplit

import pytest

from film_iq.approval import Preview, sync_one
from film_iq.movary_write import MovaryWriteBackend


@pytest.mark.parametrize(
    "response",
    [
        (500, {}),
        (200, {"results": [], "currentPage": 1, "maxPage": 1}),
        (200, {"results": [{"ids": {"tmdb": 123}}], "currentPage": 1, "maxPage": 1}),
        (200, {"results": [], "currentPage": 1, "maxPage": 2}),
    ],
)
def test_search_failure_never_writes(response: tuple[int, object]) -> None:
    calls: list[str] = []

    def transport(method: str, path: str, body: object) -> tuple[int, object]:
        calls.append(method)
        return response

    preview = Preview("Example", 123)
    with pytest.raises(ValueError):
        sync_one(
            preview, MovaryWriteBackend(preview, "user", transport), execute=True, approved=True
        )
    assert calls == ["GET"]


def test_later_watchlist_page_and_read_failure() -> None:
    calls: list[str] = []

    def transport(method: str, path: str, body: object) -> tuple[int, object]:
        calls.append(method)
        page = int(parse_qs(urlsplit(path).query)["page"][0])
        if "search" in path:
            return 200, {
                "results": [{"ids": {"tmdb": 123, "movary": 456}}],
                "currentPage": 1,
                "maxPage": 1,
            }
        return 200, {
            "watchlist": [{"movie": {"ids": {"movary": 999}}}] * 100
            if page == 1
            else [{"movie": {"ids": {"movary": 456}}}],
            "currentPage": page,
            "maxPage": 2,
        }

    preview = Preview("Example", 123)
    assert (
        sync_one(
            preview, MovaryWriteBackend(preview, "user", transport), execute=True, approved=True
        )
        == "already on watchlist"
    )
    assert calls == ["GET", "GET", "GET"]
