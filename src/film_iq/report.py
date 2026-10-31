"""Build a dry-run viewing report from accepted evidence and supplied snapshots."""

import sqlite3
from dataclasses import asdict
from typing import Any

from film_iq.planning.assertions import assertion_access
from film_iq.planning.integration import planner_film
from film_iq.planning.models import Access, Film, Plan
from film_iq.planning.monthly import compare
from film_iq.planning.personal import apply_personal
from film_iq.planning.report_dates import planning_dates
from film_iq.planning.report_offers import _offers
from film_iq.recognition.reader import current_components
from film_iq.scoring import Score, score
from film_iq.scoring.a1 import load_evidence


def _film(db: sqlite3.Connection, result: Score, catalog: dict[str, Any]) -> Film:
    item = catalog[result.film_id]
    if not isinstance(item, dict):
        raise ValueError(f"catalog entry {result.film_id} must be an object")
    if not isinstance(item["title"], str) or not item["title"].strip():
        raise ValueError("catalog titles must be nonblank")
    if type(item["minutes"]) is not int or type(item["watched"]) is not bool:
        raise ValueError("catalog needs integer minutes and boolean watched status")
    return planner_film(db, result, item["title"], item["minutes"], item["watched"])


def _validate_inputs(inputs: dict[str, Any]) -> None:
    _validate_containers(inputs)
    values = [inputs[key] for key in ("max_minutes", "max_films", "budget_cents")]
    values.extend(inputs["current_services"])
    values.extend(value for value in inputs["service_prices_cents"].values() if value is not None)
    if any(type(value) is not int or value < 0 for value in values):
        raise ValueError("limits, provider IDs and service prices must be nonnegative integers")


def _validate_containers(inputs: dict[str, Any]) -> None:
    if not isinstance(inputs, dict):
        raise ValueError("report inputs must be an object")
    for key in ("catalog", "offers", "service_prices_cents", "rental_prices_cents"):
        if not isinstance(inputs.get(key), dict):
            raise ValueError(f"{key} must be an object")
    for key in ("dates", "current_services"):
        if not isinstance(inputs.get(key), list):
            raise ValueError(f"{key} must be an array")


def _catalog(db: sqlite3.Connection, results: tuple[Score, ...], inputs: dict) -> dict:
    return {r.film_id: _film(db, r, inputs["catalog"]) for r in results if r.independent_count}


def _crosswalk(catalog: dict[str, Film]) -> dict[str, int]:
    return {key: film.id for key, film in catalog.items()}


def _previews(plans: tuple[Plan, ...]) -> dict[str, list[str]]:
    return {
        plan.option: [
            f"Preview: add {choice.film.title} (TMDB {choice.film.id}) to watchlist"
            for choice in plan.choices
        ]
        for plan in plans
    }


def build_report(
    db: sqlite3.Connection,
    inputs: dict[str, Any],
    *,
    snapshot: dict | None = None,
    refresh_status: dict | None = None,
) -> dict:
    """Use current accepted evidence; never mutate the database or watchlist.

    Catalog runtimes, watched status, provider snapshots, prices and viewing slots
    are caller-supplied facts. Missing offer responses remain unknown.
    """
    _validate_inputs(inputs)
    results = score(load_evidence(db))
    catalog = _catalog(db, results, inputs)
    films = apply_personal(list(catalog.values()), snapshot, refresh_status)
    observations, access = _offers(films, inputs)
    assertions = []
    if "assertions" in inputs:
        assertions, access = assertion_access(inputs)
    plans, verified = _comparisons(films, access, inputs)
    return {
        "mode": "dry-run",
        "crosswalk": _crosswalk(catalog),
        "evidence": [asdict(result) for result in results],
        "public_evidence_components": current_components(db),
        "offers": observations,
        "assertions": assertions,
        "service_price_assumptions": {
            str(key): value for key, value in inputs["service_prices_cents"].items()
        },
        "plans": [asdict(plan) for plan in plans],
        "verified_plans": [asdict(plan) for plan in verified],
        "films": [asdict(film) for film in films],
        "personal_refresh": snapshot["last_successful_refresh"] if snapshot else None,
        "previews": _previews(plans),
        "assumptions": "Caller-supplied snapshots; price, entitlement and expiry are shown per choice. Legacy snapshots: TMDB / JustWatch attribution.",
    }


def _comparisons(films: list[Film], access: list[Access], inputs: dict):
    parameters = (
        films,
        access,
        set(inputs["current_services"]),
        planning_dates(inputs),
        inputs["max_minutes"],
        inputs["max_films"],
        inputs["budget_cents"],
        {int(key): value for key, value in inputs["service_prices_cents"].items()},
    )
    power = inputs.get("utility_power", 1)
    plans = compare(*parameters, utility_power=power)
    verified = compare(*parameters, utility_power=power, verified_only=True)
    return plans, verified
