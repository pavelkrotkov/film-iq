"""Synthetic search pagination regressions."""

from urllib.parse import parse_qs, urlsplit

import pytest

from film_iq.approval import Preview
from film_iq.movary_write import MovaryWriteBackend


@pytest.mark.parametrize("selected", [123, 9999])
@pytest.mark.parametrize("failure", [False, True])
def test_search_extra_page_requires_exact_identity_and_success(
    selected: int, failure: bool
) -> None:
    calls: list[str] = []

    def transport(method: str, path: str, body: object) -> tuple[int, object]:
        calls.append(method)
        page = int(parse_qs(urlsplit(path).query)["page"][0])
        if "search" not in path:
            return 200, {"watchlist": [], "currentPage": 1, "maxPage": 1}
        if page == 3 and failure:
            return 500, {}
        ids = list(range(123, 143)) if page == 1 else ([143] if page == 2 else [])
        return 200, {
            "results": [{"ids": {"tmdb": i, "movary": i + 1000}} for i in ids],
            "currentPage": page,
            "maxPage": 3,
        }

    preview = Preview("Example", selected)
    backend = MovaryWriteBackend(preview, "user", transport)
    if selected == 123 and not failure:
        assert backend.find_movie(selected) == 1123
    else:
        with pytest.raises(ValueError):
            backend.find_movie(selected)
    assert calls == ["GET", "GET", "GET"]
