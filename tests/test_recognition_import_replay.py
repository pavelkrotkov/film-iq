"""The actual CLI preserves independent typed annotations on routine source replay."""

import json
from dataclasses import asdict, replace

import pytest
from recognition_support import NOW, REVIEW
from test_curated_csv import MANIFEST, body

from film_iq.cli import main
from film_iq.ingest.accept import accept
from film_iq.ingest.acquisition import acquisition_status
from film_iq.ingest.audit import AuditAttestation
from film_iq.recognition.models import AwardOutcome, ReceptionMetric
from film_iq.recognition.storage import classify_entry
from film_iq.storage import connect


def inputs(tmp_path):
    csv, manifest = tmp_path / "source.csv", tmp_path / "source.json"
    csv.write_text(
        "\n".join(
            body(
                rank="",
                tie="",
                tmdb_id="123",
                identity_reviewer="fixture reviewer",
                identity_evidence="synthetic identity",
            ).splitlines()[:2]
        )
        + "\n"
    )
    manifest.write_text(
        json.dumps(asdict(replace(MANIFEST, expected_count=1, evidence_kind="unknown")))
    )
    database = tmp_path / "evidence.db"
    return database, [
        "import-list",
        "--csv",
        str(csv),
        "--manifest",
        str(manifest),
        "--persist",
        str(database),
    ]


@pytest.mark.parametrize(
    "component",
    [
        AwardOutcome(
            "Fixture award",
            "2025",
            "Best Actor",
            "prize",
            recipient="Fixture person",
            recipient_kind="person",
        ),
        ReceptionMetric("Fixture positivity", "critics", "positivity", 87, "percent", 100),
    ],
)
def test_cli_unknown_manifest_replay_preserves_typed_review_and_cursor(tmp_path, capsys, component):
    database, args = inputs(tmp_path)
    main(args)
    original = json.loads(capsys.readouterr().out)
    revision = original["revision_id"]
    with connect(database) as db:
        entry = db.execute(
            "SELECT entry_id FROM entry_observation WHERE revision_id=?", (revision,)
        ).fetchone()[0]
        classify_entry(db, entry, revision, component, REVIEW)
        accept(
            db,
            revision,
            AuditAttestation(REVIEW.auditor, REVIEW.evidence, NOW, True, True, 1),
            previous_revision_id=None,
        )
        annotation = db.execute("SELECT kind,payload,review FROM entry_recognition").fetchone()
    main(args)
    repeated = json.loads(capsys.readouterr().out)
    with connect(database) as db:
        assert repeated["revision_id"] == revision
        assert (
            db.execute("SELECT kind,payload,review FROM entry_recognition").fetchone() == annotation
        )
        assert db.execute(
            "SELECT (SELECT count(*) FROM extraction_revision), (SELECT count(*) FROM entry_observation), (SELECT count(*) FROM entry_recognition), (SELECT count(*) FROM acquisition_attempt)"
        ).fetchone() == (1, 1, 1, 2)
        state = acquisition_status(db)[0]
        assert (state["outcome"], state["cursor"]) == ("success", revision)
