"""Read-only acquisition status preserves failures and previous successful cursors."""

import json
import sqlite3
from contextlib import closing

from test_acquisition import END, START, permit

from film_iq.cli import main
from film_iq.ingest.acquisition import begin_attempt, finish_attempt
from film_iq.recovery import backup


def test_failed_source_keeps_success_time_without_revealing_cursor(evidence_db, tmp_path, capsys):
    db = evidence_db
    permit(db)
    first = begin_attempt(db, "s", START)
    finish_attempt(db, first, END, "success", revision_id="rev", cursor="private-secret")
    second = begin_attempt(db, "s", END)
    finish_attempt(db, second, END, "error", error_code="private-error")
    query = "SELECT id,outcome,cursor FROM acquisition_attempt ORDER BY id"
    expected_rows = db.execute(query).fetchall()
    path = tmp_path / "status-copy.db"
    backup(db, path)
    before = path.read_bytes()
    assert main(["status", "--database", str(path), "--format", "json"]) == 1
    output = capsys.readouterr().out
    result = json.loads(output)["acquisition"]
    assert (result["failed"], result["cursors_present"], result["last_successful_acquisition"]) == (
        1,
        1,
        END,
    )
    assert "private" not in output and path.read_bytes() == before
    with closing(sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)) as inspected:
        assert inspected.execute(query).fetchall() == expected_rows
