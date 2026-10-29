import json

import pytest
from test_scoring_a1 import accepted

from film_iq.cli import main
from film_iq.report import build_report


def inputs():
    return {
        "catalog": {"42": {"title": "Fixture film", "minutes": 90, "watched": False}},
        "checked_at": "2026-10-29T12:00:00+00:00",
        "offers": {
            "1": {
                "id": 1,
                "results": {
                    "US": {
                        "link": "https://example.test/watch",
                        "free": [{"provider_id": 7, "provider_name": "Fixture"}],
                        "rent": [{"provider_id": 8, "provider_name": "Rental"}],
                    }
                },
            }
        },
        "current_services": [],
        "dates": ["2026-11-01"],
        "max_minutes": 90,
        "max_films": 1,
        "budget_cents": 500,
        "service_prices_cents": {},
        "rental_prices_cents": {"1:8": 400},
    }


def test_cli_report_is_read_only_with_citations(evidence_db, tmp_path, capsys):
    accepted(evidence_db)
    evidence_db.execute("UPDATE film_index SET tmdb_id=1")
    evidence_db.commit()
    before = tuple(evidence_db.iterdump())
    path = tmp_path / "inputs.json"
    path.write_text(json.dumps(inputs()))
    assert (
        main(
            [
                "report",
                "--database",
                str(tmp_path / "evidence.db"),
                "--inputs",
                str(path),
                "--format",
                "json",
            ]
        )
        == 0
    )
    result = json.loads(capsys.readouterr().out)
    assert (
        result["mode"] == "dry-run"
        and result["evidence"][0]["contributing"][0]["url"] == "https://example.test/list"
    )
    assert result["plans"][0]["option"] == "no purchase"
    assert result["plans"][0]["choices"][0]["offer"]["entitlement"] == "unconfirmed"
    assert tuple(evidence_db.iterdump()) == before


def test_missing_offer_remains_unknown(evidence_db):
    accepted(evidence_db)
    evidence_db.execute("UPDATE film_index SET tmdb_id=1")
    data = inputs()
    data["offers"] = {}
    report = build_report(evidence_db, data)
    assert report["offers"][0]["status"] == "unknown"
    assert all(not plan["choices"] for plan in report["plans"])
    data["catalog"]["42"]["watched"] = "false"
    with pytest.raises(ValueError, match="boolean watched"):
        build_report(evidence_db, data)
