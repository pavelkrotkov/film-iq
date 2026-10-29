"""Search extra-page and incomplete-response cases for pinned Movary."""

from urllib.parse import parse_qs, urlsplit

import pytest

from film_iq.approval import Preview, sync_one
from film_iq.movary_write import MovaryWriteBackend


@pytest.mark.parametrize(
    ("sizes", "failed_page", "selected", "succeeds"),
    [
        ([20, 20, 1, 0], 0, 123, True),
        ([20, 20, 1, 0], 0, 9999, False),
        ([20, 20, 1, 0], 3, 123, False),
        ([20, 20, 1, 0], 4, 123, False),
        ([20, 0, 1, 0], 0, 123, False),
        ([20, 19, 1, 0], 0, 123, False),
        ([20, 20, 2, 0], 0, 123, False),
        ([20] * 20 + [19, 0, 0], 0, 123, True),
        ([20] * 20 + [19, 0, 0], 22, 123, False),
        ([20] * 20 + [19, 0, 0], 23, 123, False),
        ([20] * 20 + [19, 0, 1], 0, 123, False),
        ([20] * 20 + [19, 0, 0, 0], 0, 123, False),
    ],
)
def test_search_pages(sizes: list[int], failed_page: int, selected: int, succeeds: bool) -> None:
    calls: list[str] = []

    def transport(method: str, path: str, body: object) -> tuple[int, object]:
        calls.append(method)
        page = int(parse_qs(urlsplit(path).query)["page"][0])
        if page == failed_page:
            return 500, {}
        start = 123 + (page - 1) * 20
        results = [
            {"ids": {"tmdb": i, "movary": i + 1000}} for i in range(start, start + sizes[page - 1])
        ]
        return 200, {"results": results, "currentPage": page, "maxPage": len(sizes)}

    preview = Preview("Example", selected)
    backend = MovaryWriteBackend(preview, "user", transport)
    if succeeds:
        assert backend.find_movie(selected) == 1123
        assert len(calls) == len(sizes)
    else:
        with pytest.raises(ValueError):
            sync_one(preview, backend, execute=True, approved=True)
    assert all(method == "GET" for method in calls)
