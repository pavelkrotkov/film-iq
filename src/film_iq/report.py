"""Build a dry-run viewing report from accepted evidence and supplied snapshots."""

import sqlite3
from dataclasses import asdict
from datetime import date, datetime
from typing import Any

from film_iq.availability.tmdb import Offer, normalize
from film_iq.planning.integration import planner_film
from film_iq.planning.models import Access, Film, Plan
from film_iq.planning.monthly import compare
from film_iq.scoring import Score, score
from film_iq.scoring.a1 import load_evidence


def _film(db: sqlite3.Connection, result: Score, catalog: dict[str, Any]) -> Film:
    item = catalog[result.film_id]
    if not isinstance(item["title"], str) or not item["title"].strip():
        raise ValueError("catalog titles must be nonblank")
    if type(item["minutes"]) is not int or type(item["watched"]) is not bool:
        raise ValueError("catalog needs integer minutes and boolean watched status")
    return planner_film(db, result, item["title"], item["minutes"], item["watched"])


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


def _validate_inputs(inputs: dict[str, Any]) -> None:
    values = [inputs[key] for key in ("max_minutes", "max_films", "budget_cents")]
    values.extend(inputs["current_services"])
    values.extend(inputs["service_prices_cents"].values())
    if any(type(value) is not int or value < 0 for value in values):
        raise ValueError("limits, provider IDs and service prices must be nonnegative integers")


def _previews(plans: tuple[Plan, ...]) -> dict[str, list[str]]:
    return {
        plan.option: [
            f"Preview: add {choice.film.title} (TMDB {choice.film.id}) to watchlist"
            for choice in plan.choices
        ]
        for plan in plans
    }


def build_report(db: sqlite3.Connection, inputs: dict[str, Any]) -> dict:
    """Use current accepted evidence; never mutate the database or watchlist.

    Catalog runtimes, watched status, provider snapshots, prices and viewing slots
    are caller-supplied facts. Missing offer responses remain unknown.
    """
    _validate_inputs(inputs)
    results = score(load_evidence(db))
    films = [_film(db, result, inputs["catalog"]) for result in results if result.independent_count]
    observations, access = _offers(films, inputs)
    plans = compare(
        films,
        access,
        set(inputs["current_services"]),
        [date.fromisoformat(value) for value in inputs["dates"]],
        inputs["max_minutes"],
        inputs["max_films"],
        inputs["budget_cents"],
        {int(key): value for key, value in inputs["service_prices_cents"].items()},
    )
    return {
        "mode": "dry-run",
        "evidence": [asdict(result) for result in results],
        "offers": observations,
        "plans": [asdict(plan) for plan in plans],
        "previews": _previews(plans),
        "assumptions": "Caller-supplied snapshots; TMDB / JustWatch attribution; prices and entitlement unverified",
    }
