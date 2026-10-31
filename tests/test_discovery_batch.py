"""A repeated work keeps both ballots but appears once in the viewing shortlist."""

from dataclasses import replace

from discovery_fixtures import fresh_status, snapshot
from test_curated_csv import MANIFEST, body

from film_iq.discovery_batch import build_discoveries
from film_iq.ingest.accept import accept
from film_iq.ingest.audit import AuditAttestation
from film_iq.ingest.curated import import_list


def selection(db, edition):
    csv = body(
        edition=edition,
        tmdb_id="123",
        identity_reviewer="fixture auditor",
        identity_evidence="synthetic reviewed work identity",
    )
    csv = "\n".join(csv.splitlines()[:2]) + "\n"
    manifest = replace(MANIFEST, edition=edition, expected_count=1)
    preview = import_list(csv, manifest, db=db, accessed_at="2026-10-31T00:00:00Z")
    accept(
        db,
        preview["revision_id"],
        AuditAttestation(
            "independent fixture", "complete synthetic ballot", "2026-10-31", True, True, 1
        ),
        previous_revision_id=None,
    )
    db.execute("UPDATE source SET independence_verification='verified' WHERE id='critic'")
    db.execute(
        "UPDATE published_list SET lineage_kind='original',lineage_verification='verified' WHERE source_id='critic'"
    )
    return preview


def test_repeated_work_keeps_source_reasons_without_extra_suggestions(evidence_db):
    cohorts = [selection(evidence_db, edition) for edition in ("2023-a", "2024-a")]
    report = build_discoveries(cohorts, snapshot(), db=evidence_db, refresh_status=fresh_status())
    assert (report["total_candidates"], report["unique_films"], report["accepted"]) == (2, 1, 2)
    assert len(report["suggested_unwatched"]) == 1
    film = report["suggested_unwatched"][0]
    assert {row["edition"] for row in film["source_reasons"]} == {"2023-a", "2024-a"}
    assert film["external_critical_recognition"]["independent_count"] == 1
    assert len(report["cohorts"]) == 2
    assert (
        build_discoveries(cohorts, snapshot(True), db=evidence_db, refresh_status=fresh_status())[
            "suggested_unwatched"
        ]
        == []
    )
