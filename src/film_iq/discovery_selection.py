"""Preserve unresolved selections and deduplicate only reviewed work identities."""

from film_iq.discovery_works import coalesce_works


def remaining(report):
    suggested = {item["tmdb_id"] for item in report["suggested_unwatched"]}
    return coalesce_works(
        item
        for item in report["candidates"]
        if item["identity_status"] != "reviewed" or item["tmdb_id"] not in suggested
    )
