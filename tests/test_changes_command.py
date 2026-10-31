"""Output must succeed before a local consumer acknowledges changes."""

import json

from test_accept import pending
from test_acquisition import END, permit

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
