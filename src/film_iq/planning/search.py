"""Small exhaustive bundle search."""

from dataclasses import replace
from datetime import date
from itertools import combinations, product

from .models import Access, Choice, Film, Plan


def _schedule(
    choices: tuple[tuple[Film, Access], ...], dates: tuple[date, ...]
) -> tuple[Choice, ...] | None:
    ordered = sorted(choices, key=lambda pair: pair[1].expires or date.max)
    if any(
        offer.expires is not None and day > offer.expires
        for (_, offer), day in zip(ordered, dates, strict=False)
    ):
        return None
    return tuple(
        Choice(film, offer, day) for (film, offer), day in zip(ordered, dates, strict=False)
    )


def _bundles(available: list[tuple[Film, list[Access]]], limit: int):
    # ponytail: exhaustive search suits small POC shortlists; use a solver if scale demands it.
    for count in range(1, min(len(available), limit) + 1):
        for group in combinations(available, count):
            for selected in product(*(os for _, os in group)):
                yield tuple((item[0], o) for item, o in zip(group, selected, strict=True))


def _better(schedule: tuple[Choice, ...] | None, utility: float, cost: int, best: Plan) -> bool:
    return schedule is not None and (utility, -cost) > (best.utility, -best.cost_cents)


def _rental_cost(bundle: tuple[tuple[Film, Access], ...]) -> int:
    return sum(o.price_cents or 0 for _, o in bundle if o.kind == "rent")


def _best(
    label: str,
    fee: int,
    available: list[tuple[Film, list[Access]]],
    slots: tuple[date, ...],
    max_minutes: int,
    max_films: int,
    budget: int,
) -> Plan:
    best = Plan(
        label, (), 0, fee, 0, "USD cents; prices include tax; unconfirmed entitlement is tentative"
    )
    for bundle in _bundles(available, min(len(slots), max_films)):
        minutes = sum(f.minutes for f, _ in bundle)
        cost = fee + _rental_cost(bundle)
        if max(minutes - max_minutes, cost - budget) > 0:
            continue
        schedule = _schedule(bundle, slots)
        utility = sum(f.score for f, _ in bundle)
        if _better(schedule, utility, cost, best):
            best = Plan(label, schedule or (), minutes, cost, utility, best.assumptions)
    return replace(best, feasibility=_feasibility(best))


def _feasibility(plan: Plan):
    return (
        "tentative" if any(c.offer.entitlement != "confirmed" for c in plan.choices) else "verified"
    )
