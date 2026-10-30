"""Inspect deduplicated discovery and separately qualified purchasing advice."""

from datetime import datetime

from .assertion import Assertion
from .opportunity import Opportunity


def purchase_ready(item: Assertion) -> bool:
    """Require reviewed work, confirmed exact access and explicit price/currency."""
    offer = item.opportunity
    plan_known = offer.kind not in {"subscription", "add-on"} or offer.plan is not None
    add_on_known = offer.kind != "add-on" or offer.add_on is not None
    return (
        item.work_status == "reviewed"
        and item.entitlement == "confirmed"
        and plan_known
        and add_on_known
        and item.price_minor is not None
        and item.currency is not None
    )


def opportunities(assertions: tuple[Assertion, ...]) -> dict[Opportunity, tuple[Assertion, ...]]:
    """Deduplicate opportunities while retaining source claims and disagreements."""
    result: dict[Opportunity, list[Assertion]] = {}
    for item in dict.fromkeys(assertions):
        result.setdefault(item.opportunity, []).append(item)
    return {key: tuple(values) for key, values in result.items()}


def first_seen_by_us(assertions: tuple[Assertion, ...]) -> datetime | None:
    return min((item.checked_at for item in assertions), default=None)
