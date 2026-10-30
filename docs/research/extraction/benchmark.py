"""Evaluate synthetic extraction completeness and source semantics."""

from collections import Counter

from docs.research.extraction.model import Entry, Evaluation


def field_accuracy(
    expected: list[Entry], actual: list[Entry], field: str, matches: int
) -> float | None:
    if not matches:
        return None
    wanted = Counter((entry.key, getattr(entry, field)) for entry in expected)
    received = Counter((entry.key, getattr(entry, field)) for entry in actual)
    return sum((wanted & received).values()) / matches


def evaluate(expected: list[Entry], actual: list[Entry]) -> Evaluation:
    """Compare stable source entry keys and independently check entry semantics."""
    wanted = Counter(entry.key for entry in expected)
    if not wanted or any(count != 1 for count in wanted.values()):
        raise ValueError("Expected entries must have unique keys and cannot be empty")
    received = Counter(entry.key for entry in actual)
    matches = sum((wanted & received).values())
    exact = sum((Counter(expected) & Counter(actual)).values())
    fields = ("title", "rank", "tie", "category", "lineage")
    return {
        "precision": matches / len(actual) if actual else None,
        "recall": matches / len(expected),
        "fields": {field: field_accuracy(expected, actual, field, matches) for field in fields},
        "complete": len(actual) == len(expected) == matches == exact,
    }
