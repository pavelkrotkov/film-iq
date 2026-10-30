"""Only explicit viewing-date merit tags are personal artistic judgment."""

import re

_TAG = re.compile(r"Artistic merit: (10|[1-9])/10(?![\w/]|[.,]\d)")


def merit(rows: list[dict[str, str]]) -> tuple[int | None, str]:
    """Repeated plays on one date are one assertion; conflicting dates need review."""
    entries = {(row["watchedAt"], row["comment"]) for row in rows}
    scores: set[int] = set()
    invalid = False
    for _, comment in entries:
        matches = _TAG.findall(comment)
        invalid |= comment.count("Artistic merit:") != len(matches)
        scores.update(map(int, matches))
    if len(scores) > 1:
        return None, "conflict"
    if invalid:
        return None, "invalid"
    return (next(iter(scores)), "known") if scores else (None, "unknown")
