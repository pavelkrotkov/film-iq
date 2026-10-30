"""Inspect deduplicated discovery and separately qualified purchasing advice."""

from datetime import datetime, timedelta

from .assertion import Assertion
from .opportunity import Opportunity
from .timing import purchase_window


def purchase_ready(item: Assertion, *, now: datetime, max_age: timedelta) -> bool:
    """Require qualified access within supplied freshness and asserted availability."""
    offer = item.opportunity
    plan_known = offer.kind not in {"subscription", "add-on"} or offer.plan is not None
    add_on_known = offer.kind != "add-on" or offer.add_on is not None
    return all(
        (
            item.work_status == "reviewed",
            item.entitlement == "confirmed",
            plan_known,
            add_on_known,
            item.price_minor is not None,
            item.currency is not None,
            purchase_window(item, now, max_age),
        )
    )


def opportunities(assertions: tuple[Assertion, ...]) -> dict[Opportunity, tuple[Assertion, ...]]:
    """Deduplicate opportunities while retaining source claims and disagreements."""
    result: dict[Opportunity, list[Assertion]] = {}
    for item in dict.fromkeys(assertions):
        result.setdefault(item.opportunity, []).append(item)
    return {key: tuple(values) for key, values in result.items()}


def first_seen_by_us(assertions: tuple[Assertion, ...]) -> datetime | None:
    return min((item.checked_at for item in assertions), default=None)
