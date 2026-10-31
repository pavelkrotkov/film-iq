"""The scheduled CLI must retain every selected ballot through the real report."""

import json
from unittest.mock import Mock

from discovery_fixtures import fresh_status, snapshot
from test_discovery_batch import selection

from film_iq import operations, operations_run


def test_multiple_cohorts_reach_report_and_backup(evidence_db, tmp_path, monkeypatch):
    paths = []
    for edition in ("2023-a", "2024-a"):
        cohort = selection(evidence_db, edition)
        path = tmp_path / f"{edition}.json"
        path.write_text(json.dumps(cohort))
        paths.extend(["--cohort", str(path)])
    evidence_db.commit()
    personal = tmp_path / "snapshot.json"
    personal.write_text(json.dumps(snapshot()))
    personal.with_suffix(".json.status").write_text(json.dumps(fresh_status()))
    monkeypatch.setattr(operations, "_required_env", lambda key: "fixture")
    monkeypatch.setattr(operations_run, "refresh", Mock())
    report, backups = tmp_path / "report.md", tmp_path / "backups"
    args = [
        "--database",
        str(tmp_path / "evidence.db"),
        "--snapshot",
        str(personal),
        "--report",
        str(report),
        "--backups",
        str(backups),
        "--status",
        str(tmp_path / "run.status"),
        "--ratings-csv",
        "unused",
        "--history-csv",
        "unused",
        *paths,
    ]
    assert operations.main(args) == 0
    rendered = report.read_text()
    assert "2023-a" in rendered and "2024-a" in rendered
    assert rendered.count("### [Synthetic film") == 1
    assert len(list(backups.glob("*.db"))) == 1
