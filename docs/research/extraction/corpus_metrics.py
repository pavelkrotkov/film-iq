"""Compare source-entry multisets and complete displayed observations."""

from collections import Counter

FIELDS = ("title", "position", "rank", "tie", "category")


def record_counts(rows: list[dict]) -> Counter:
    return Counter(tuple(r[f] for f in FIELDS) for r in rows)


def measure(expected: list[dict], actual: list[dict]) -> dict:
    if not expected:
        raise ValueError("An empty oracle cannot establish completeness")
    wanted = Counter(r["title"] for r in expected)
    received = Counter(r["title"] for r in actual)
    matches = sum((wanted & received).values())
    exact = record_counts(expected)
    result = record_counts(actual)
    return {
        "expected": len(expected),
        "extracted": len(actual),
        "matched_titles": matches,
        "entry_precision": matches / len(actual) if actual else None,
        "entry_recall": matches / len(expected),
        "exact_records": sum((exact & result).values()),
        "fields": {f: field_matches(expected, actual, f) / len(expected) for f in FIELDS},
        "complete": expected == actual,
    }


def field_matches(expected: list[dict], actual: list[dict], field: str) -> int:
    wanted = Counter((r["title"], r[field]) for r in expected)
    received = Counter((r["title"], r[field]) for r in actual)
    return sum((wanted & received).values())
