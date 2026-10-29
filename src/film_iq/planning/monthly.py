"""Compare small feasible bundles using supplied scores, dates and prices."""

from datetime import date

from .models import Access, Film, Plan
from .search import _best


def _eligible(offer: Access, current: set[int], service: int | None, rentals: bool) -> bool:
    if offer.entitlement == "unavailable_on_plan":
        return False
    if offer.kind in {"free", "ads"}:
        return True
    if offer.kind == "rent":
        return rentals and offer.price_cents is not None
    return offer.kind == "subscription" and offer.provider_id in current | (
        {service} if service is not None else set()
    )


def _validate(films: list[Film], offers: list[Access], values: list[int]) -> None:
    if min(values, default=0) < 0:
        raise ValueError("capacities and prices must be nonnegative")
    if min(map(lambda f: f.minutes, films), default=1) <= 0:
        raise ValueError("films need positive runtimes")
    if len({f.id for f in films}) != len(films):
        raise ValueError("films need unique IDs and positive runtimes")
    for offer in offers:
        if (offer.price_cents or 0) < 0:
            raise ValueError("offer prices must be nonnegative")


def _available(
    films: list[Film], offers: list[Access], current: set[int], service: int | None, rentals: bool
) -> list[tuple[Film, list[Access]]]:
    result = []
    for film in films:
        choices = [
            o for o in offers if o.film_id == film.id and _eligible(o, current, service, rentals)
        ]
        if not film.watched and film.score > 0 and choices:
            result.append((film, choices))
    return result


def compare(
    films: list[Film],
    offers: list[Access],
    current: set[int],
    dates: list[date],
    max_minutes: int,
    max_films: int,
    budget_cents: int,
    services: dict[int, int],
) -> tuple[Plan, ...]:
    """Compare positive-score bundles with caller-provided viewing slots and total USD prices.

    Costs break utility ties. Unconfirmed entitlement is tentative, not verified.
    """
    _validate(films, offers, [max_minutes, max_films, budget_cents, *services.values()])
    slots = tuple(sorted(set(dates)))
    options: list[tuple[str, int | None, bool, int]] = [
        ("no purchase", None, False, 0),
        ("rentals", None, True, 0),
    ]
    options += [
        (f"service {s}", s, False, price)
        for s, price in sorted(services.items())
        if s not in current
    ]
    return tuple(
        _best(
            label,
            fee,
            _available(films, offers, current, service, rentals),
            slots,
            max_minutes,
            max_films,
            budget_cents,
        )
        for label, service, rentals, fee in options
        if fee <= budget_cents
    )
