"""Access/quota failures stop immediately without removing prior comparable offers."""

from dataclasses import replace

import pytest
from candidate_support import WORK, native_payload, permit, response
from discovery_offer_support import observation
from offer_store_support import NOW

from film_iq.availability.candidate_run import run_candidates
from film_iq.availability.ledger import save_fetch
from film_iq.availability.state import read_state


@pytest.mark.parametrize(
    "status,headers",
    [
        (401, {}),
        (429, {}),
    ],
)
def test_access_or_known_exhaustion_stops_and_retains_baseline(
    evidence_db, monkeypatch, status, headers
):
    permit(evidence_db)
    prior = observation(source="motn")
    save_fetch(evidence_db, prior, NOW)
    monkeypatch.setenv("MOVIE_OF_THE_NIGHT_API_KEY", "fixture-secret")
    get = response(native_payload(), status, headers)
    result = run_candidates(
        evidence_db,
        "motn",
        [WORK, replace(WORK, tmdb_id=124, imdb_id="tt0000124")],
        max_requests=2,
        live=True,
        now=NOW,
        get=get,
    )
    assert (result["requests"], get.call_count) == (1, 1)
    assert result["results"][1]["status"] == "not_requested_after_stop"
    assert read_state(evidence_db, prior, NOW)["current"]["assertions"]
    assert evidence_db.execute(
        "SELECT count(*) FROM offer_event WHERE json_extract(payload, '$.kind')='source_absent'"
    ).fetchone() == (0,)
