"""Explicit utility and purchase options, without fitted personal preferences."""

from math import isfinite

from .models import Access, Film
from .prices import validate_free_price


def options(current: set[int], services: dict[int, int | None]):
    result: list[tuple[str, int | None, bool, int]] = [
        ("no purchase", None, False, 0),
        ("rentals", None, True, 0),
    ]
    result += [
        (f"service {s}{suffix}", s, rentals, price)
        for s, price in sorted(services.items())
        if s not in current and price is not None
        for suffix, rentals in (("", False), (" + rentals", True))
    ]
    return result


def validate_utility(films: list[Film], power: float) -> None:
    """Validate declared recognition utility without mutating source/personal inputs."""
    if not isfinite(power) or power <= 0:
        raise ValueError("utility_power must be finite and positive")
    if any(not isfinite(film.score) or film.score < 0 for film in films):
        raise ValueError("film scores must be finite and nonnegative")


def known_inputs(offers: list[Access], services: dict[int, int | None], verified_only: bool):
    for offer in offers:
        validate_free_price(offer.kind, offer.price_cents)
    prices = [price for price in services.values() if price is not None]
    if verified_only:
        offers = [offer for offer in offers if verified_access(offer)]
    return offers, prices


def verified_access(offer: Access) -> bool:
    """Current entitlement alone cannot verify a future dated viewing choice."""
    return offer.entitlement == "confirmed" and offer.expires is not None
