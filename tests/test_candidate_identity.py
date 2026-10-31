"""Exact reviewed IDs and explicit country response are required before positive claims."""

from candidate_support import WORK, native_payload
from offer_store_support import NOW

from film_iq.availability.candidate_native import normalize


def test_native_crosswalk_mismatch_is_unknown():
    field, value = "tmdbId", "movie/999"
    payload = native_payload()
    payload[field] = value
    observed = normalize(WORK, payload, NOW)
    assert observed.status == "unknown" and observed.assertions == ()
