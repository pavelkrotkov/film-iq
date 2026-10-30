"""Reject inconsistent metadata throughout an advertised empty search tail."""

from urllib.parse import parse_qs, urlsplit

import pytest

from film_iq.approval import Preview
from film_iq.movary_write import MovaryWriteBackend


@pytest.mark.parametrize("bad_page", [22, 23])
@pytest.mark.parametrize("field", ["currentPage", "maxPage"])
def test_search_tail_rejects_bad_metadata(bad_page: int, field: str) -> None:
    def transport(method: str, path: str, body: object) -> tuple[int, object]:
        page = int(parse_qs(urlsplit(path).query)["page"][0])
        size = 20 if page <= 20 else 19 if page == 21 else 0
        results = [
            {"ids": {"tmdb": i, "movary": i + 1000}}
            for i in range(123 + (page - 1) * 20, 123 + (page - 1) * 20 + size)
        ]
        response = {"results": results, "currentPage": page, "maxPage": 23}
        if page == bad_page:
            response[field] = 99
        return 200, response

    with pytest.raises(ValueError):
        MovaryWriteBackend(Preview("Example", 123), "user", transport).find_movie(123)
