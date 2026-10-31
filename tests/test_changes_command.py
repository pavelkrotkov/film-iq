"""Output must succeed before a local consumer acknowledges changes."""

import json

from test_accept import pending
from test_acquisition import END, permit

from film_iq.changes_checkpoint import checkpoint
from film_iq.cli import main


def arguments(tmp_path):
    return [
        "changes",
        "--database",
        str(tmp_path / "evidence.db"),
        "--checkpoint",
        str(tmp_path / "seen.json"),
        "--now",
        END,
        "--format",
        "json",
    ]


def test_preview_then_explicit_baseline_ack_is_private(evidence_db, tmp_path, capsys):
    # Preview intentionally leaves first-use baseline creation to explicit acknowledgement.
    pending(evidence_db)
    permit(evidence_db)
    args = arguments(tmp_path)
    assert main(args) == 0
    assert json.loads(capsys.readouterr().out)["baseline"]
    path = tmp_path / "seen.json"
    assert not path.exists()


def test_explicit_baseline_ack_is_private_and_read_only(evidence_db, tmp_path, capsys):
    pending(evidence_db)
    permit(evidence_db)
    before = tuple(evidence_db.iterdump())
    args = arguments(tmp_path)
    path = tmp_path / "seen.json"
    assert main([*args, "--ack"]) == 0
    assert json.loads(capsys.readouterr().out)["baseline"]
    assert checkpoint(path) == {"source_revisions": {"list": "rev"}, "offer_events": []}
    assert path.stat().st_mode & 0o777 == 0o600
    assert main(args) == 0
    result = json.loads(capsys.readouterr().out)
    assert not result["baseline"] and not result["source_changes"]
    assert tuple(evidence_db.iterdump()) == before
