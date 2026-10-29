import pytest
from test_report import inputs
from test_scoring_a1 import accepted

from film_iq.report import build_report
from film_iq.report_render import markdown


@pytest.mark.parametrize(
    "field,value",
    [
        ("offers", None),
        ("offers", []),
        ("service_prices_cents", []),
        ("catalog", []),
        ("dates", {}),
        ("current_services", None),
    ],
)
def test_invalid_containers_fail_explicitly(evidence_db, field, value):
    data = inputs()
    data[field] = value
    with pytest.raises(ValueError, match=field):
        build_report(evidence_db, data)


def test_report_links_plan_to_evidence(evidence_db):
    accepted(evidence_db)
    evidence_db.execute("UPDATE film_index SET tmdb_id=1")
    result = build_report(evidence_db, inputs())
    assert result["crosswalk"] == {"42": 1}
    rendered = markdown(result)
    assert "Film 42 → TMDB 1" in rendered and "https://example.test/list" in rendered
    assert "Fixture film (TMDB 1)" in rendered and "no purchase" in rendered
    assert "unconfirmed" in rendered and "uncalibrated" in rendered


def test_watched_films_have_no_watchlist_preview(evidence_db):
    accepted(evidence_db)
    evidence_db.execute("UPDATE film_index SET tmdb_id=1")
    data = inputs()
    data["catalog"]["42"]["watched"] = True
    report = build_report(evidence_db, data)
    assert all(not previews for previews in report["previews"].values())
