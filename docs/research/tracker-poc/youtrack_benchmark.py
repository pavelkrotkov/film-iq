"""Measure complete local YouTrack fixture traversal and numeric sorting."""

import time

from youtrack_client import YouTrackClient, YouTrackError
from youtrack_enrich import custom_value


def main() -> None:
    client = YouTrackClient()
    started = time.monotonic()
    rows = client.pages(
        "issues",
        query={
            "fields": "id,customFields(name,value)",
            "query": "project: {FILMPOC} has: {FilmIQ Critic Score} sort by: {FilmIQ Critic Score} desc",
        },
    )
    elapsed = time.monotonic() - started
    scores = [custom_value(issue, "FilmIQ Critic Score") for issue in rows]
    if len(scores) != 1000 or not all(type(value) is int for value in scores):
        raise YouTrackError("The complete synthetic scoring dataset was not returned")
    if scores != sorted(scores, reverse=True):
        raise YouTrackError("YouTrack did not return numeric descending order")
    print(f"YouTrack: {len(rows)} fixture records paged and sorted numerically in {elapsed:.3f}s")


if __name__ == "__main__":
    main()
