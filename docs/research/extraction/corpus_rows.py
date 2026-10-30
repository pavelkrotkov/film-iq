"""Static film-row selectors developed without the held-out sections."""

import re
from html import unescape

from docs.research.extraction.html_element import Element


def heading(value: str) -> str:
    return unescape(re.sub("<[^>]+>", "", value))


def title(node: Element) -> str | None:
    first = next(node.elements("i"), None)
    return first.text() if first else None


def row_rank(row: Element) -> int | None:
    cells = [c for c in row.children if isinstance(c, Element) and c.tag in {"td", "th"}]
    first = cells[0].text() if cells else ""
    return int(first) if first.isdigit() else None


def table_rows(tree: Element, category: str) -> list[tuple[str, int | None, str]]:
    rows = []
    for row in tree.elements("tr"):
        film = title(row)
        headers = list(row.elements("th"))
        if film:
            rows.append((film, row_rank(row), category))
        elif len(headers) == 1 and int(headers[0].attrs.get("colspan") or "1") > 1:
            category = headers[0].text()
    return rows


def list_rows(tree: Element, category: str, ranked: bool) -> list[tuple[str, int | None, str]]:
    rows = []
    rank = 0
    for node in tree.elements("li"):
        film = title(node)
        if film:
            rank = int(node.attrs.get("value") or rank + 1)
            rows.append((film, rank if ranked else None, category))
    return rows
