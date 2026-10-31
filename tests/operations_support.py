"""Disposable installation inputs for scheduler failure/locking checks."""

from unittest.mock import Mock

from film_iq import operations_run
from film_iq.storage import connect, migrate


def configuration(tmp_path, monkeypatch):
    database = tmp_path / "evidence.db"
    with connect(database) as db:
        migrate(db)
    refresh = Mock()
    monkeypatch.setattr(operations_run, "refresh", refresh)
    monkeypatch.setattr(operations_run, "discovery_command", Mock(return_value="Private shortlist"))
    return refresh, {
        "database": database,
        "cohort": tmp_path / "cohort.json",
        "snapshot": tmp_path / "snapshot.json",
        "report": tmp_path / "report.md",
        "backups": tmp_path / "backups",
        "status": tmp_path / "run.status",
    }
