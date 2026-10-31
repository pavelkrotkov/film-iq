"""Producer names are readable without changing stable service/add-on identity."""

import pytest
from candidate_support import WORK, native_payload, native_row, permit, response
from discovery_offer_support import configure, report
from offer_store_support import NOW

from film_iq.availability.candidate_run import run_candidates


@pytest.mark.parametrize("provider", ["tmdb", "motn"])
def test_source_names_reach_cards_while_ids_stay_in_audit(
    evidence_db, tmp_path, monkeypatch, provider
):
    configure(evidence_db, tmp_path)
    permit(evidence_db, provider)
    monkeypatch.setenv("TMDB_READ_ACCESS_TOKEN", "fixture-secret")
    monkeypatch.setenv("MOVIE_OF_THE_NIGHT_API_KEY", "fixture-secret")
    tmdb = {
        "id": 123,
        "results": {
            "US": {
                "link": "https://example.test/watch",
                "flatrate": [{"provider_id": 7, "provider_name": "Fixture Stream"}],
            }
        },
    }
    native = native_payload(
        [
            native_row(
                type="addon", addon={"id": "fixture-extra", "name": "Fixture Extra"}, price=None
            )
        ]
    )
    get = response(tmdb if provider == "tmdb" else native)
    run_candidates(evidence_db, provider, [WORK], max_requests=1, live=True, now=NOW, get=get)
    result = report(tmp_path)
    claim = result["candidates"][0]["offer_states"][0]["latest_attempt"]["assertions"][0]
    main = report(tmp_path, output_format="markdown").split("<details>", 1)[0]
    assert claim["opportunity"]["service"] == ("tmdb:7" if provider == "tmdb" else "fixture")
    assert (
        "Fixture Stream" if provider == "tmdb" else "Fixture Cinema / tier unknown / Fixture Extra"
    ) in main
    assert "service ID" not in main
