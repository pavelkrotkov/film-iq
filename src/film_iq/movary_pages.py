"""Read complete paginated Movary responses through an injected request.

The reported current page must match each requested page. The reported maximum
must remain stable through the read. Inconsistent or partial responses raise
instead of implying absence. Movary 0.82.1 search alone permits a trailing
empty page when its pagination calculation advertises one extra page.
The empty first page is accepted when the server reports zero or one pages.
These checks do not provide a snapshot when the remote collection changes.
"""

from collections.abc import Callable
from urllib.parse import urlencode


def object_data(value: object) -> dict:
    if not isinstance(value, dict):
        raise ValueError("Invalid Movary response")
    return value


def _bounds(rows: list, page: int, last: int, maximum: int | None, *, trailing: bool) -> None:
    if last < 0 or (maximum is not None and last != maximum):
        raise ValueError("Inconsistent Movary pagination")
    if not (trailing and not rows and page == last and maximum == last):
        _page_bounds(rows, page, last)


def _page_bounds(rows: list, page: int, last: int) -> None:
    if last == 0:
        if page != 1 or rows:
            raise ValueError("Inconsistent Movary pagination")
        return
    if last > 0 and page > last:
        raise ValueError("Inconsistent Movary pagination")
    _nonempty(rows, page, last)


def _nonempty(rows: list, page: int, last: int) -> None:
    if not rows and (page > 1 or page < last):
        raise ValueError("Incomplete Movary page")


def _page(
    data: object, key: str, page: int, maximum: int | None, *, trailing: bool = False
) -> tuple[list, int]:
    data = object_data(data)
    rows, current, last = data.get(key), data.get("currentPage"), data.get("maxPage")
    if not isinstance(rows, list) or type(current) is not int or type(last) is not int:
        raise ValueError("Invalid Movary pagination")
    if current != page:
        raise ValueError("Inconsistent Movary pagination")
    _bounds(rows, page, last, maximum, trailing=trailing)
    return rows, last


def _search_extra_page(sizes: list[int], maximum: int | None) -> bool:
    """Validate TMDB page sizes and the pinned Movary max-page calculation."""
    if len(sizes) < 2 or not 0 < sizes[-1] < 20:
        return False
    if any(size != 20 for size in sizes[:-1]) or maximum != len(sizes) + 1:
        return False
    total = sum(sizes)
    limit = total // len(sizes)
    return (total + limit - 1) // limit == maximum


def pages(
    request: Callable[[str], object], path: str, key: str, params: dict, *, search: bool = False
) -> list:
    entries: list = []
    page, maximum = 1, None
    sizes: list[int] = []
    while True:
        query = urlencode({**params, "page": page})
        trailing = search and _search_extra_page(sizes, maximum)
        rows, last = _page(request(f"{path}?{query}"), key, page, maximum, trailing=trailing)
        if key == "watchlist" and page < last and len(rows) < params["limit"]:
            raise ValueError("Incomplete Movary page")
        sizes.append(len(rows))
        entries.extend(rows)
        if page >= last:
            return entries
        maximum, page = last, page + 1
