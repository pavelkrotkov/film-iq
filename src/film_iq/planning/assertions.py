"""Adapt reviewed source assertions to explicitly identified service-plan choices."""

from dataclasses import asdict
from datetime import datetime, timedelta

from film_iq.availability.access_check import purchase_ready
from film_iq.availability.assertion import Assertion
from film_iq.availability.opportunity import Opportunity
from film_iq.availability.timing import purchase_window
from film_iq.planning.models import Access
from film_iq.planning.prices import validate_free_price


def assertion_access(inputs: dict) -> tuple[list[dict], list[Access]]:
    """Keep audit assertions intact; only fresh reviewed US work enters planning.

    Each numeric provider ID identifies one exact service/plan/add-on combination,
    not all tiers from that company. Caller prices remain explicit assumptions.
    """
    now = datetime.fromisoformat(inputs["assessed_at"])
    hours = inputs["offer_max_age_hours"]
    if type(hours) not in {int, float} or hours < 0:
        raise ValueError("offer_max_age_hours must be nonnegative")
    age = timedelta(hours=hours)
    observations, access, plans = [], [], {}
    for index, raw in enumerate(inputs["assertions"]):
        identifier, assertion = _parse(raw)
        _plan(plans, identifier, assertion.opportunity)
        _subscription_price(inputs, identifier, assertion)
        observations.append({"provider_id": identifier, **asdict(assertion)})
        if _eligible(assertion, now, age):
            access.append(_access(identifier, assertion, now, age, index))
    return observations, access


def _parse(raw: dict) -> tuple[int, Assertion]:
    data = dict(raw)
    identifier = data.pop("provider_id")
    if type(identifier) is not int or identifier <= 0:
        raise ValueError("assertion provider IDs must be positive integers")
    data["opportunity"] = Opportunity(**data["opportunity"])
    for field in ("checked_at", "asserted_added_on", "asserted_expires_at"):
        if data.get(field) is not None:
            data[field] = datetime.fromisoformat(data[field])
    assertion = Assertion(**data)
    validate_free_price(assertion.opportunity.kind, assertion.price_minor)
    return identifier, assertion


def _plan(plans: dict, identifier: int, offer: Opportunity) -> None:
    identity = offer.service, offer.plan, offer.add_on
    if identifier in plans and plans[identifier] != identity:
        raise ValueError("one provider ID cannot merge different services, tiers or add-ons")
    if any(key != identifier and value == identity for key, value in plans.items()):
        raise ValueError("one service/plan/add-on must use one provider ID")
    plans[identifier] = identity


def _eligible(item: Assertion, now: datetime, age: timedelta) -> bool:
    return (
        item.opportunity.country == "US"
        and item.opportunity.kind not in {"buy", "library"}
        and item.work_status == "reviewed"
        and purchase_window(item, now, age)
        and item.currency in {None, "USD"}
    )


def _access(identifier: int, item: Assertion, now: datetime, age: timedelta, index: int) -> Access:
    kind = item.opportunity.kind
    if kind == "library":
        raise ValueError("library borrowing is not a priced planner option")
    expiry = item.asserted_expires_at
    # Date-only scheduling cannot prove a slot before an intraday expiry.
    expires = (expiry - timedelta(days=1)).date() if expiry else None
    entitlement = item.entitlement
    if entitlement == "confirmed" and not purchase_ready(item, now=now, max_age=age):
        entitlement = "unconfirmed"
    return Access(
        item.opportunity.film_id,
        identifier,
        kind,
        entitlement,
        item.price_minor if item.currency == "USD" else None,
        expires,
        index,
    )


def _subscription_price(inputs: dict, identifier: int, item: Assertion) -> None:
    if item.opportunity.kind != "subscription" or identifier in inputs["current_services"]:
        return
    declared = inputs["service_prices_cents"].get(str(identifier))
    if declared is not None and (declared, "USD") != (item.price_minor, item.currency):
        raise ValueError("subscription fee must match the exact plan's USD price assertion")
