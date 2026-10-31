"""Attach permitted source claims to reviewed works without planning or account inference."""

import sqlite3
from datetime import datetime

from film_iq.availability.codec import timestamp
from film_iq.availability.retained import retained_states


def attach_offers(report: dict, db: sqlite3.Connection, now: datetime) -> dict:
    grouped: dict[int, list[dict]] = {}
    for state in retained_states(db, now):
        latest = state["latest_attempt"]
        grouped.setdefault(latest["film_id"], []).append(state)
    candidates = [_attach(item, grouped) for item in report["candidates"]]
    if not any("offer_states" in item for item in candidates):
        return report
    return {
        **report,
        "offer_assessed_at": timestamp(now),
        "options": [
            "No purchase / no new service; source-reported US access and attempt details accompany the films, without purchase advice."
        ],
        "candidates": candidates,
        "suggested_unwatched": [_attach(item, grouped) for item in report["suggested_unwatched"]],
    }


def _attach(item: dict, grouped: dict[int, list[dict]]) -> dict:
    if item["identity_status"] != "reviewed":
        return item
    states = [
        state
        for state in grouped.get(item["tmdb_id"], [])
        if _reviewed(state) and state["latest_attempt"]["country"] == "US"
    ]
    return (
        {
            **item,
            "offer_states": states,
            "access": "source-reported US claims; entitlement and freshness require verification",
        }
        if states
        else item
    )


def _reviewed(state: dict) -> bool:
    return any(
        record and record["work_reviewed"] for record in (state["current"], state["latest_attempt"])
    )
