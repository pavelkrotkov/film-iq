"""Adapt the existing tentative TMDB normalizer to scoped canonical observations."""

from datetime import datetime

from film_iq.availability.assertion import Assertion
from film_iq.availability.candidate_fields import link
from film_iq.availability.candidate_models import ReviewedWork
from film_iq.availability.fetch import Fetch
from film_iq.availability.opportunity import Opportunity
from film_iq.availability.tmdb import normalize as tmdb_normalize
from film_iq.availability.validation import positive_id


def normalize(work: ReviewedWork, payload: dict, checked_at: datetime) -> Fetch:
    if type(payload.get("id")) is not int:
        return Fetch("tmdb", work.tmdb_id, "US", checked_at, "unknown", work_reviewed=True)
    observed = tmdb_normalize(work.tmdb_id, payload, checked_at)
    assertions, partial = [], observed.status == "partial"
    for row in observed.offers:
        try:
            positive_id(row.provider_id)
            offer = Opportunity(work.tmdb_id, f"tmdb:{row.provider_id}", row.kind, "US")
            assertions.append(
                Assertion(offer, "tmdb", checked_at, link(row.url), work_status="reviewed")
            )
        except (ValueError, TypeError):
            partial = True
    status = "partial" if partial else observed.status
    return Fetch(
        "tmdb", work.tmdb_id, "US", checked_at, status, tuple(assertions), work_reviewed=True
    )
