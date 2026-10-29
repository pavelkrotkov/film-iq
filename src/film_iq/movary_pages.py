"""Read complete paginated Movary responses through an injected request.

The reported current page must match each requested page. The reported maximum
must remain stable through the read and every advertised page must contain
entries. Inconsistent or partial responses raise instead of implying absence.
The empty first page is accepted when the server reports zero or one pages.
These checks do not provide a snapshot when the remote collection changes.
"""

from collections.abc import Callable
from urllib.parse import urlencode


def object_data(value: object) -> dict:
    if not isinstance(value, dict):
        raise ValueError("Invalid Movary response")
    return value


def _bounds(rows: list, page: int, last: int, maximum: int | None) -> None:
    if last < 0 or (maximum is not None and last != maximum):
        raise ValueError("Inconsistent Movary pagination")
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


def _page(data: object, key: str, page: int, maximum: int | None) -> tuple[list, int]:
    data = object_data(data)
    rows, current, last = data.get(key), data.get("currentPage"), data.get("maxPage")
    if not isinstance(rows, list) or type(current) is not int or type(last) is not int:
        raise ValueError("Invalid Movary pagination")
    if current != page:
        raise ValueError("Inconsistent Movary pagination")
    _bounds(rows, page, last, maximum)
    return rows, last


def pages(request: Callable[[str], object], path: str, key: str, params: dict) -> list:
    entries: list = []
    page, maximum = 1, None
    while True:
        query = urlencode({**params, "page": page})
        rows, last = _page(request(f"{path}?{query}"), key, page, maximum)
        entries.extend(rows)
        if page >= last:
            return entries
        maximum, page = last, page + 1
