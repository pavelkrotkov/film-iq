"""A killed write cannot leave partial observations, baseline or events."""

import os
import subprocess
import sys
from pathlib import Path

from offer_store_support import NOW, fetch, prepare

from film_iq.availability.ledger import save_fetch
from film_iq.storage import connect, migrate


def test_killed_observation_transaction_can_be_retried(evidence_db, tmp_path):
    prepare(evidence_db)
    database = tmp_path / "evidence.db"
    script = """
import os, sys
from film_iq.availability import ledger
from film_iq.storage import connect
from offer_store_support import NOW, fetch
ledger._advance = lambda *args: os._exit(19)
ledger.save_fetch(connect(__import__('pathlib').Path(sys.argv[1])), fetch(), NOW)
"""
    env = {
        **os.environ,
        "PYTHONPATH": os.pathsep.join((str(Path.cwd() / "src"), str(Path.cwd() / "tests"))),
    }
    result = subprocess.run([sys.executable, "-c", script, str(database)], env=env, check=False)
    assert result.returncode == 19
    with connect(database) as db:
        for table in ("offer_fetch", "offer_current", "offer_event"):
            assert db.execute(f"SELECT count(*) FROM {table}").fetchone() == (0,)
        save_fetch(db, fetch(), NOW)
        assert db.execute("SELECT count(*) FROM offer_event").fetchone() == (1,)


def test_schema_nine_upgrade_preserves_evidence(evidence_db):
    evidence_db.executescript("""
        DROP TABLE offer_event; DROP TABLE offer_current;
        DROP TABLE offer_fetch; DROP TABLE offer_purge; DROP TABLE offer_policy;
        PRAGMA user_version=9;
    """)
    migrate(evidence_db)
    migrate(evidence_db)
    assert evidence_db.execute("PRAGMA user_version").fetchone() == (10,)
    assert evidence_db.execute("SELECT raw_title FROM entry_observation").fetchone() == (
        "Unchanged title",
    )
    assert evidence_db.execute("PRAGMA foreign_key_check").fetchall() == []
