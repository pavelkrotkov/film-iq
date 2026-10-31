"""Preserve unresolved selections and deduplicate only reviewed work identities."""


def _unique(items):
    selected, seen = [], set()
    for item in items:
        key = item["tmdb_id"] if item["identity_status"] == "reviewed" else None
        if key is None or key not in seen:
            selected.append(item)
        seen.add(key)
    return selected


def remaining(report):
    suggested = {item["tmdb_id"] for item in report["suggested_unwatched"]}
    return _unique(
        item
        for item in report["candidates"]
        if item["identity_status"] != "reviewed" or item["tmdb_id"] not in suggested
    )
