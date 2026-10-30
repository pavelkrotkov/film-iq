import os
import subprocess
import sys
from pathlib import Path

from test_acquisition import END, START, permit

from film_iq.ingest.acquisition import acquisition_status, begin_attempt, finish_attempt


def test_killed_process_restarts_without_partial_evidence(evidence_db):
    db = evidence_db
    permit(db)
    path = db.execute("PRAGMA database_list").fetchone()[2]
    program = """
import os, sqlite3, sys
from film_iq.ingest.acquisition import begin_attempt
connection = sqlite3.connect(sys.argv[1])
connection.execute('PRAGMA foreign_keys=ON')
begin_attempt(connection, 's', sys.argv[2])
connection.execute("UPDATE entry_observation SET raw_title='uncommitted'")
os._exit(7)
"""
    environment = dict(os.environ, PYTHONPATH=str(Path(__file__).parents[1] / "src"))
    result = subprocess.run([sys.executable, "-c", program, path, START], env=environment)
    assert result.returncode == 7
    assert acquisition_status(db)[0]["outcome"] == "running"
    assert db.execute("SELECT raw_title FROM entry_observation").fetchone() == ("Unchanged title",)
    interrupted = str(acquisition_status(db)[0]["attempt_id"])
    finish_attempt(db, interrupted, END, "unknown", error_code="interrupted")
    resumed = begin_attempt(db, "s", END)
    finish_attempt(db, resumed, END, "success", revision_id="rev", cursor="resumed")
    assert acquisition_status(db)[0]["cursor"] == "resumed"
    assert db.execute("SELECT count(*) FROM entry_observation").fetchone() == (1,)
