"""Accepted films stay browsable independently of optional personal-history state."""

from typing import cast

from film_iq.discovery_order import Order, ordered_suggestions
from film_iq.discovery_works import coalesce_works
from film_iq.recognition.reader import KINDS

KIND_LABELS = {
    "critic_selection": "Critics & polls",
    "institutional_selection": "Festivals & institutions",
    "registry_selection": "Preservation",
    "award_outcome": "Awards",
    "reception_metric": "Reception",
    "unknown": "Unclassified source",
}
WATCHED = {
    "unwatched": "Not marked watched",
    "all": "All films",
    "watched": "Watched",
    "unknown": "Unknown history",
}


def films(report: dict, order: str = "public-support") -> list[dict]:
    # Preview claims cannot grant identity or extraction acceptance.
    items = coalesce_works(
        item
        for item in report["candidates"]
        if item["extraction_status"] == "accepted" and item["identity_status"] == "reviewed"
    )
    # Old snapshots retain useful dates, but cannot establish current exclusion.
    # Use unknown for both labels and filters after a failed refresh.
    if report["personal_state_stale"]:
        items = [{**item, "watched": None} for item in items]
    return ordered_suggestions(items, cast(Order, order))


def kinds(item: dict) -> set[str]:
    # A multi-source film may be both a critic pick and a preservation selection.
    source = {reason["evidence_kind"] for reason in item["source_reasons"]}
    return source | {kind for kind in KINDS if item.get("public_evidence_components", {}).get(kind)}


def watched_label(item: dict) -> str:
    return {True: "Watched", False: "Not watched", None: "Watch history unknown"}[item["watched"]]


def filters(query: dict[str, list[str]]) -> dict[str, str]:
    # Restrict query enums before passing an order into the discovery contract.
    values = {
        key: query.get(key, [default])[0]
        for key, default in (
            ("q", ""),
            ("kind", "all"),
            ("watched", "unwatched"),
            ("order", "public-support"),
        )
    }
    if values["kind"] not in {"all", *KIND_LABELS} or values["watched"] not in WATCHED:
        raise ValueError("Unknown film filter")
    if values["order"] not in {"source", "public-support"}:
        raise ValueError("Unknown ordering")
    return values


def select(items: list[dict], values: dict[str, str]) -> list[dict]:
    query = values["q"].strip().casefold()
    return [
        item
        for item in items
        if query in searchable(item)
        and (values["kind"] == "all" or values["kind"] in kinds(item))
        and matches_watched(item, values["watched"])
    ]


def searchable(item: dict) -> str:
    display = item.get("display") or {}
    names = [display.get("title"), display.get("original_title"), *display.get("directors", [])]
    source = item["source_reasons"] + [
        row
        for kind in (*KINDS, "unclassified")
        for row in item.get("public_evidence_components", {}).get(kind, [])
    ]
    names.extend(
        value for reason in source for value in (reason["raw_title"], reason.get("director"))
    )
    return " ".join(str(name) for name in names if name).casefold()


def matches_watched(item: dict, choice: str) -> bool:
    return {
        "all": True,
        "unwatched": item["watched"] is not True,
        "watched": item["watched"] is True,
        "unknown": item["watched"] is None,
    }[choice]
