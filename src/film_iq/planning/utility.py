"""Explicit utility and purchase options, without fitted personal preferences."""

from dataclasses import replace
from math import isfinite

from .models import Access, Film


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


def utility(films: list[Film], power: float) -> list[Film]:
    """User-declared recognition utility; personal scores remain separate inputs."""
    if not isfinite(power) or power <= 0:
        raise ValueError("utility_power must be finite and positive")
    if any(not isfinite(film.score) or film.score < 0 for film in films):
        raise ValueError("film scores must be finite and nonnegative")
    if power == 1:
        return films
    return [
        replace(
            film,
            score=film.score**power,
            utility_assumption=f"{film.utility_assumption}; recognition-power-v1 power={power}; "
            "personal enjoyment and artistic merit preserved separately, not fitted or blended",
        )
        for film in films
    ]


def known_inputs(offers: list[Access], services: dict[int, int | None], verified_only: bool):
    prices = [price for price in services.values() if price is not None]
    if verified_only:
        offers = [offer for offer in offers if offer.entitlement == "confirmed"]
    return offers, prices
