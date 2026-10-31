"""Recoverable local execution; no Movary writes or provider acquisition."""

import fcntl
import json
import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from film_iq.discovery_command import discovery_command
from film_iq.movary import MovaryClient
from film_iq.operations_write import private_text
from film_iq.personal_io import private_json
from film_iq.personal_refresh import refresh
from film_iq.recovery import backup
from film_iq.storage import connect, migrate


def run_once(
    client: MovaryClient,
    *,
    database: Path,
    cohort: Path,
    snapshot: Path,
    report: Path,
    backups: Path,
    status: Path,
    **exports,
) -> dict:
    """Serialize this installation's scheduled runs; retain prior outputs on failure."""
    status.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with status.with_suffix(status.suffix + ".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        previous = json.loads(status.read_text()) if status.exists() else {}
        state = {
            "version": "private-run-v1",
            "attempted_at": datetime.now(UTC).isoformat(),
            "last_successful_run": previous.get("last_successful_run"),
            "stale": True,
        }
        private_json(status, state)
        return _execute(client, database, cohort, snapshot, report, backups, status, state, exports)


def _execute(client, database, cohort, snapshot, report, backups, status, state, exports):
    try:
        with closing(connect(database)) as db:
            migrate(db)
        refresh(client, snapshot, **exports)
        output = discovery_command(cohort, snapshot, database, "markdown")
        backups.mkdir(parents=True, exist_ok=True, mode=0o700)
        destination = backups / f"evidence-{uuid4().hex}.db"
        with closing(connect(database)) as db:
            backup(db, destination)
        private_text(report, output)
    except (OSError, ValueError, KeyError, TypeError, sqlite3.Error, RuntimeError):
        private_json(status, {**state, "error": "run_failed"})
        raise RuntimeError("Private run failed; prior successful report retained") from None
    state.update(
        stale=False,
        last_successful_run=datetime.now(UTC).isoformat(),
        evidence_backup=str(destination),
    )
    private_json(status, state)
    return state
