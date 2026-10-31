"""Pure native-v4 candidate mapping; no provider choice, request or rights grant."""

from dataclasses import replace
from datetime import datetime

from film_iq.availability.assertion import Assertion
from film_iq.availability.candidate_fields import link, money, seconds
from film_iq.availability.candidate_models import ReviewedWork
from film_iq.availability.fetch import Fetch
from film_iq.availability.opportunity import Opportunity


def normalize(work: ReviewedWork, payload: dict, checked_at: datetime) -> Fetch:
    empty = Fetch(
        "motn",
        work.tmdb_id,
        "US",
        checked_at,
        "unknown",
        work_reviewed=True,
        catalog_scope="public_country",
    )
    if (payload.get("tmdbId"), payload.get("imdbId"), payload.get("showType")) != (
        f"movie/{work.tmdb_id}",
        work.imdb_id,
        "movie",
    ):
        return empty
    options = payload.get("streamingOptions")
    if not isinstance(options, dict):
        return empty
    rows = options.get("us")
    if not isinstance(rows, list):
        return empty
    assertions, partial = [], False
    for row in rows:
        try:
            assertions.append(_assertion(work, row, checked_at))
        except (ValueError, TypeError, KeyError, AttributeError, OverflowError):
            partial = True
    return replace(empty, status="partial" if partial else "complete", assertions=tuple(assertions))


def _assertion(work: ReviewedWork, row: dict, checked_at: datetime) -> Assertion:
    if row["type"] not in {"subscription", "free", "rent", "buy", "addon"}:
        raise ValueError("unsupported native offer type")
    kind = "add-on" if row["type"] == "addon" else row["type"]
    addon = row["addon"]["id"] if kind == "add-on" else None
    price, currency = money(row.get("price"))
    offer = Opportunity(
        work.tmdb_id, row["service"]["id"], kind, "US", add_on=addon, quality=row.get("quality")
    )
    return Assertion(
        offer,
        "motn",
        checked_at,
        link(row["link"]),
        price,
        currency,
        work_status="reviewed",
        service_name=row["service"].get("name"),
        addon_name=row["addon"].get("name") if kind == "add-on" else None,
        provider_detected_at=seconds(row.get("availableSince")),
        provider_last_day_at=seconds(row.get("expiresOn")),
    )
