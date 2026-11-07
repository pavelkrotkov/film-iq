"""Offline backup/restore check using only a new fictional POC database."""

import ast
import os
import sqlite3
import sys
import tempfile
from contextlib import closing
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "docs/research/tracker-poc"))
from preferences import load, validate  # noqa: E402

source_code = (ROOT / "docs/research/tracker-poc/preferences.py").read_text()
tree = ast.parse(source_code)
schemas = [
    node.value
    for node in ast.walk(tree)
    if isinstance(node, ast.Constant)
    and isinstance(node.value, str)
    and node.value.startswith("CREATE TABLE IF NOT EXISTS preferences (")
]
if len(schemas) != 1:
    raise RuntimeError("Cannot uniquely identify the current POC schema")

cache = ROOT / ".cache/tracker-poc"
cache.mkdir(mode=0o700, parents=True, exist_ok=True)
directory = Path(tempfile.mkdtemp(prefix="synthetic-pref-recovery-", dir=cache))
source, archive, restored = (
    directory / name for name in ("source.sqlite3", "archive.sqlite3", "restored.sqlite3")
)
for item in (source, archive, restored):
    fd = os.open(item, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(fd)

expected = validate(
    {
        "interest_score": 8,
        "watchlist": None,
        "watched_at": "2026-10-01T12:34:00+00:00",
        "personal_notes": "Fictional recovery test note.",
    }
)
user, task = "fictional-user", "fictional-film"
with closing(sqlite3.connect(source)) as db, closing(sqlite3.connect(archive)) as backup:
    db.execute("PRAGMA journal_mode=WAL")
    db.execute(schemas[0])
    db.execute(
        "INSERT INTO preferences VALUES (?,?,?,?,?,?)",
        (
            user,
            task,
            expected["interest_score"],
            -1,
            expected["watched_at"],
            expected["personal_notes"],
        ),
    )
    db.commit()
    assert load(db, user, task) == expected
    db.backup(backup)
    assert load(backup, user, task) == expected
with closing(sqlite3.connect(archive)) as backup, closing(sqlite3.connect(restored)) as destination:
    backup.backup(destination)
    assert destination.execute("PRAGMA integrity_check").fetchone() == ("ok",)
    assert load(destination, user, task) == expected
    assert load(destination, "unrelated-fictional-user", task) == {
        "interest_score": None,
        "watchlist": None,
        "watched_at": None,
        "personal_notes": "",
    }
assert (archive.stat().st_mode & 0o777) == 0o600
print(
    "Fictional SQLite WAL online backup and separate restore passed; POC load returned all four exact preference values; archive mode 0600."
)
print(f"Artifacts retained in {directory}")
