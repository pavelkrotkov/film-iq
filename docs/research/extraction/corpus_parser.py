"""Frozen baseline for static film rows, displayed ranks and groups."""

from collections import Counter

from docs.research.extraction.corpus_rows import heading, list_rows, table_rows
from docs.research.extraction.html_element import Element
from docs.research.extraction.html_tree import Tree


def extract(html: str, case: dict) -> list[dict]:
    tree = Tree(html).root
    category = heading(case["heading"])
    rows = table_rows(tree, category)
    if case["corpus_stratum"] == "nbr":
        rows = [
            (n.text(), 1 if i == 0 else None, category) for i, n in enumerate(tree.elements("i"))
        ]
    elif not rows:
        ordered = next(tree.elements("ol"), None)
        listing = ordered or next(tree.elements("ul"), Element("empty"))
        rows = list_rows(listing, category, ordered is not None)
    return records(rows)


def records(rows: list[tuple[str, int | None, str]]) -> list[dict]:
    counts = Counter(rank for _, rank, _ in rows if rank is not None)
    return [
        {
            "title": film,
            "position": i,
            "rank": rank,
            "tie": f"rank-{rank}" if rank is not None and counts[rank] > 1 else None,
            "category": group,
        }
        for i, (film, rank, group) in enumerate(rows, 1)
    ]
