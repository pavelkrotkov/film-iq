"""Attach optional reviewed display facts without changing accepted source observations."""

from datetime import datetime
from pathlib import Path

from film_iq.discovery_order import Order, ordered_suggestions, ordering_note
from film_iq.display_catalog import read_catalog


def _display(item: dict, catalog: dict[int, dict]) -> dict:
    facts = catalog.get(item["tmdb_id"]) if item["identity_status"] == "reviewed" else None
    return {**item, "display": facts}


def present_discovery(
    report: dict,
    catalog: Path | None = None,
    order: Order = "source",
    *,
    now: datetime | None = None,
) -> dict:
    facts, context = read_catalog(catalog, now)
    suggestions = [_display(item, facts) for item in report["suggested_unwatched"]]
    return {
        **report,
        "display_catalog": context,
        "ordering": {"policy": order, "explanation": ordering_note(order)},
        "candidates": [_display(item, facts) for item in report["candidates"]],
        "suggested_unwatched": ordered_suggestions(suggestions, order),
    }
