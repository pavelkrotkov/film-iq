"""Rights, dry-run and batch validation gate every request and ledger write."""

from unittest.mock import Mock

import pytest
from candidate_support import WORK, manifest
from offer_store_support import NOW

from film_iq.availability import candidate_command, candidate_run
from film_iq.availability.candidate_run import run_candidates


def test_source_policy_blocks_transport_and_persistence(evidence_db):
    evidence_db.commit()
    before = tuple(evidence_db.iterdump())
    get = Mock()
    with pytest.raises(PermissionError):
        run_candidates(evidence_db, "motn", [WORK], max_requests=1, live=True, now=NOW, get=get)
    assert get.call_count == 0
    assert tuple(evidence_db.iterdump()) == before


def test_cli_dry_run_opens_no_database_or_credential(tmp_path, monkeypatch, capsys):
    path = manifest(tmp_path / "works.json")
    monkeypatch.setattr(
        candidate_run, "request", Mock(side_effect=AssertionError("must not build request"))
    )
    database = tmp_path / "missing.db"
    assert (
        candidate_command.main(
            [
                "--provider",
                "motn",
                "--input",
                str(path),
                "--database",
                str(database),
                "--max-requests",
                "1",
            ]
        )
        == 0
    )
    assert "dry_run" in capsys.readouterr().out
    assert not database.exists()
