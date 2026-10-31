"""Explicit synthetic-copy inventory, not a production artifact registry."""

import json
import sqlite3
import tarfile
from contextlib import closing
from dataclasses import replace
from datetime import timedelta

from offer_store_support import EXPIRY, NOW, fetch, policy, prepare

from film_iq.availability.ledger import save_fetch
from film_iq.availability.policies import record_policy
from film_iq.availability.state import read_state
from film_iq.recovery import backup, restore


def copies(db, root):
    prepare(db)
    identifier = save_fetch(db, fetch(), NOW)
    # Renewal permits fresh checks without extending this original observation.
    renewed = replace(policy(allowed=True), expires_at=EXPIRY + timedelta(days=30))
    record_policy(db, replace(renewed, source="unrelated"), NOW)
    unrelated = save_fetch(db, fetch(source="unrelated"), NOW)
    record_policy(db, renewed, NOW)
    assert save_fetch(db, fetch(), NOW) == identifier
    deadline = db.execute(
        "SELECT expires_at FROM offer_fetch WHERE id=?", (identifier,)
    ).fetchone()[0]
    payload = json.dumps(read_state(db, fetch(), NOW))
    for name in ("report.json", "export.json"):
        (root / name).write_text(payload)
    backup(db, root / "online.sqlite")
    with tarfile.open(root / "archive.tar", "w") as archive:
        archive.add(root / "online.sqlite", arcname="online.sqlite")
    with tarfile.open(root / "archive.tar") as archive:
        archive.extractall(root / "isolated", filter="data")
    restore(root / "isolated/online.sqlite", root / "restored.sqlite")
    names = [
        "report.json",
        "export.json",
        "online.sqlite",
        "archive.tar",
        "isolated/online.sqlite",
        "restored.sqlite",
    ]
    manifest = {"source": "fixture", "expires_at": deadline, "names": names}
    (root / "retention-manifest.json").write_text(json.dumps(manifest))
    return identifier, unrelated, names, deadline


def copied_deadline(path, identifier):
    with closing(sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)) as db:
        return db.execute(
            "SELECT expires_at FROM offer_fetch WHERE id=?", (identifier,)
        ).fetchone()[0]
