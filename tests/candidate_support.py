"""Synthetic reviewed candidate and provider payloads; never live catalog data."""

import json
from dataclasses import asdict
from unittest.mock import Mock

from offer_store_support import NOW, policy

from film_iq.availability.candidate_models import ReviewedWork
from film_iq.availability.policies import record_policy

WORK = ReviewedWork(
    123, "tt0000123", "Synthetic independent auditor", "Synthetic fixture crosswalk", True
)


def native_row(**changes):
    return {
        "type": "rent",
        "service": {"id": "fixture", "name": "Fixture Cinema"},
        "link": "https://example.test/film",
        "quality": "hd",
        "price": {"amount": "4.99", "currency": "USD"},
        "availableSince": int(NOW.timestamp()) - 3600,
        "expiresOn": int(NOW.timestamp()) + 172800,
        **changes,
    }


def native_payload(rows=None):
    return {
        "tmdbId": "movie/123",
        "imdbId": WORK.imdb_id,
        "showType": "movie",
        "streamingOptions": {"us": [native_row()] if rows is None else rows},
    }


def response(payload, status=200, headers=None):
    return Mock(return_value=(status, json.dumps(payload).encode(), headers or {}))


def permit(db, provider="motn", **changes):
    db.commit()
    record_policy(db, policy(provider, allowed=True, **changes), NOW)


def manifest(path, works=(WORK,)):
    path.write_text(json.dumps([asdict(work) for work in works]))
    return path
