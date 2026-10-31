"""Exact reviewed IDs and explicit country response are required before positive claims."""

import pytest
from candidate_support import WORK, native_payload
from offer_store_support import NOW

from film_iq.availability.candidate_native import normalize


@pytest.mark.parametrize(
    "field,value", [("tmdbId", "movie/999"), ("imdbId", "tt9999999"), ("showType", "series")]
)
def test_native_crosswalk_mismatch_is_unknown(field, value):
    payload = native_payload()
    payload[field] = value
    observed = normalize(WORK, payload, NOW)
    assert observed.status == "unknown" and observed.assertions == ()


@pytest.mark.parametrize("options", [None, {}, {"ca": []}, {"us": None}])
def test_missing_or_invalid_us_is_unknown(options):
    payload = native_payload()
    payload["streamingOptions"] = options
    assert normalize(WORK, payload, NOW).status == "unknown"


def test_explicit_empty_us_is_complete_but_unknown_plan_never_creates_comparison_scope():
    observed = normalize(WORK, native_payload([]), NOW)
    assert observed.status == "complete" and observed.assertions == ()
    assert observed.plan_scope is None
