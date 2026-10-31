"""Fixture HTTP response -> validated Fetch -> retained ledger -> real discovery."""

from candidate_support import WORK, native_payload, native_row, permit, response
from discovery_offer_support import configure, report
from offer_store_support import NOW

from film_iq.availability.candidate_run import run_candidates


def test_native_candidate_preserves_variants_and_provider_date_semantics(
    evidence_db, tmp_path, monkeypatch
):
    configure(evidence_db, tmp_path)
    permit(evidence_db)
    monkeypatch.setenv("MOVIE_OF_THE_NIGHT_API_KEY", "fixture-secret")
    rows = [
        native_row(),
        native_row(quality="sd", price={"amount": "2.99", "currency": "USD"}),
        native_row(
            type="addon", addon={"id": "fixture-extra", "name": "Fixture Extra"}, price=None
        ),
    ]
    get = response(native_payload(rows))
    result = run_candidates(
        evidence_db, "motn", [WORK], max_requests=1, live=True, now=NOW, get=get
    )
    assert (result["requests"], get.call_count) == (1, 1)
    output = report(tmp_path)
    state = output["candidates"][0]["offer_states"][0]
    claims = state["latest_attempt"]["assertions"]
    assert [a["price_minor"] for a in claims] == [499, 299, None]
    assert (claims[2]["opportunity"]["service"], claims[2]["opportunity"]["add_on"]) == (
        "fixture",
        "fixture-extra",
    )
    _provider_dates(claims[0])
    assert (state["current"]["plan_scope"], state["current"]["catalog_scope"]) == (
        None,
        "public_country",
    )
    rendered = report(tmp_path, output_format="markdown").split("<details>", 1)[0]
    assert "provider says last day 2026-01-03T00:00:00+00:00" in rendered
    assert "Fixture Cinema / tier unknown / Fixture Extra" in rendered
    assert (
        "[Streaming Availability API by Movie of the Night](https://www.movieofthenight.com/about/api)"
        in rendered
    )


def _provider_dates(claim):
    """Provider discovery time and last day are not effective access instants."""
    assert (claim["provider_detected_at"], claim["provider_last_day_at"]) == (
        "2025-12-31T23:00:00+00:00",
        "2026-01-03T00:00:00+00:00",
    )
    assert (claim["asserted_added_on"], claim["asserted_expires_at"]) == (None, None)
