"""Legacy tentative TMDB observations for the report planner."""

from dataclasses import asdict
from datetime import datetime
from typing import Any

from film_iq.availability.tmdb import Offer, normalize
from film_iq.planning.models import Access, Film


def _offers(films: list[Film], inputs: dict[str, Any]) -> tuple[list[dict], list[Access]]:
    observations, access = [], []
    checked = datetime.fromisoformat(inputs["checked_at"])
    for film in films:
        observation = normalize(film.id, inputs["offers"].get(str(film.id)), checked)
        observations.append({"tmdb_id": film.id, **asdict(observation)})
        # TMDB supplies neither rental prices nor plan-specific entitlement.
        access.extend(
            Access(o.film_id, o.provider_id, o.kind, "unconfirmed", _price(o, inputs))
            for o in observation.offers
        )
    return observations, access


def _price(offer: Offer, inputs: dict[str, Any]) -> int | None:
    if offer.kind != "rent":
        return None
    value = inputs["rental_prices_cents"].get(f"{offer.film_id}:{offer.provider_id}")
    if value is not None and (type(value) is not int or value < 0):
        raise ValueError("rental prices must be nonnegative integer USD cents")
    return value
