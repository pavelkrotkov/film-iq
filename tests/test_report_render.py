from test_report import inputs
from test_scoring_a1 import accepted

from film_iq.report import build_report
from film_iq.report_render import markdown


def test_report_links_plan_to_evidence(evidence_db):
    accepted(evidence_db)
    evidence_db.execute("UPDATE film_index SET tmdb_id=1")
    result = build_report(evidence_db, inputs())
    assert result["crosswalk"] == {"42": 1}
    rendered = markdown(result)
    assert "Film 42 → TMDB 1" in rendered and "https://example.test/list" in rendered
    assert "Fixture film (TMDB 1)" in rendered and "no purchase" in rendered
    assert "unconfirmed" in rendered and "uncalibrated" in rendered
    assert "extraction: not evaluated; identity: not evaluated" in rendered
    assert "evidence disagreement: not evaluated; prediction: not applicable" in rendered


def test_watched_films_have_no_watchlist_preview(evidence_db):
    accepted(evidence_db)
    evidence_db.execute("UPDATE film_index SET tmdb_id=1")
    data = inputs()
    data["catalog"]["42"]["watched"] = True
    report = build_report(evidence_db, data)
    assert all(not previews for previews in report["previews"].values())


def test_markdown_rental_joins_normalized_offer(evidence_db):
    accepted(evidence_db)
    evidence_db.execute("UPDATE film_index SET tmdb_id=1")
    data = inputs()
    del data["offers"]["1"]["results"]["US"]["free"]
    report = build_report(evidence_db, data)
    rental = report["offers"][0]["offers"][0]
    # Decoys ensure the join uses film, provider and kind, not list position.
    report["offers"][0]["offers"] = [
        {**rental, "film_id": 99, "provider": "Wrong film"},
        {**rental, "provider_id": 99, "provider": "Wrong provider"},
        {**rental, "kind": "buy", "provider": "Wrong kind"},
        rental,
    ]
    rendered = markdown(report)
    assert "rentals — USD 4.00" in rendered
    assert "rent, [Rental](https://example.test/watch) (provider 8)" in rendered
    assert "checked 2026-10-29 12:00:00+00:00 (TMDB / JustWatch)" in rendered
    assert "entitlement unconfirmed, 2026-11-01" in rendered
    assert "Wrong" not in rendered
