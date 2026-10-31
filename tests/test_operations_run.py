"""A failed scheduled run retains output; retry and overlapping runs are safe."""

import json
from unittest.mock import Mock

import pytest
from operations_support import configuration

from film_iq import operations_run
from film_iq.recovery import restore
from film_iq.storage import connect


def test_failure_then_retry_preserves_report_and_restorable_backup(tmp_path, monkeypatch):
    refresh, paths = configuration(tmp_path, monkeypatch)
    first = operations_run.run_once(Mock(), **paths)
    before = paths["report"].read_bytes()
    refresh.side_effect = ValueError("private credential must not reach status")
    with pytest.raises(RuntimeError, match="prior successful report retained"):
        operations_run.run_once(Mock(), **paths)
    failed = json.loads(paths["status"].read_text())
    assert failed["stale"] and failed["last_successful_run"] == first["last_successful_run"]
    assert "credential" not in paths["status"].read_text()
    assert paths["report"].read_bytes() == before
    refresh.side_effect = None
    recovered = operations_run.run_once(Mock(), **paths)
    assert not recovered["stale"] and "error" not in recovered
    restore(tmp_path / recovered["evidence_backup"], tmp_path / "restored.db")
    with connect(tmp_path / "restored.db") as db:
        assert db.execute("PRAGMA user_version").fetchone() == (10,)
    assert paths["report"].stat().st_mode & 0o777 == 0o600
    assert paths["status"].stat().st_mode & 0o777 == 0o600
