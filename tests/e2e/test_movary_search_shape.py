"""Malformed populated search pages must stop an approved sync before writes."""

from urllib.parse import parse_qs, urlsplit

import pytest

from film_iq.approval import Preview, sync_one
from film_iq.movary_write import MovaryWriteBackend


@pytest.mark.parametrize("sizes", [[19, 20], [21], [20, 21], [20, 19, 20]])
def test_malformed_search_shape_never_posts(sizes: list[int]) -> None:
    calls: list[str] = []

    def transport(method: str, path: str, body: object) -> tuple[int, object]:
        calls.append(method)
        page = int(parse_qs(urlsplit(path).query)["page"][0])
        start = 123 + (page - 1) * 20
        rows = [{"ids": {"tmdb": i, "movary": None}} for i in range(start, start + sizes[page - 1])]
        return 200, {"results": rows, "currentPage": page, "maxPage": len(sizes)}

    preview = Preview("Example", 123)
    with pytest.raises(ValueError):
        sync_one(
            preview, MovaryWriteBackend(preview, "user", transport), execute=True, approved=True
        )
    assert calls and all(method == "GET" for method in calls)
