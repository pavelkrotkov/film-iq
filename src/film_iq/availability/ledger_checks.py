"""Reviewed comparable scopes and temporal consistency for durable offer writes."""

from datetime import datetime

from film_iq.availability.codec import decode_fetch, timestamp
from film_iq.availability.fetch import Fetch
from film_iq.availability.opportunity import Change


def _chronology(db, fetch, scope):
    rows = db.execute(
        "SELECT checked_at,payload FROM offer_fetch WHERE scope=? AND checked_at>=?",
        (scope, timestamp(fetch.checked_at)),
    )
    for checked, old_payload in rows:
        if checked > timestamp(fetch.checked_at):
            raise ValueError("observation time moved backwards")
        if fetch.status == decode_fetch(old_payload).status == "complete":
            raise ValueError("conflicting complete observations at one timestamp require review")


def _baseline(fetch):
    return (
        fetch.status == "complete"
        and fetch.work_reviewed
        and fetch.plan_scope is not None
        and all(item.work_status == "reviewed" for item in fetch.assertions)
    )


def _initial(fetch):
    return tuple(
        Change("source_first_seen", item, fetch.source, fetch.checked_at)
        for item in sorted({a.opportunity for a in fetch.assertions}, key=repr)
    )


def _validate_time(fetch: Fetch, now: datetime) -> None:
    if type(fetch.work_reviewed) is not bool:
        raise ValueError("work_reviewed must be boolean")
    if fetch.checked_at > now or any(
        item.checked_at > fetch.checked_at for item in fetch.assertions
    ):
        raise ValueError("observation/assertion time is in the future")
