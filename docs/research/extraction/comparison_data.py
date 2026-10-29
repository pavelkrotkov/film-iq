"""Fictional incremental input and transactional SQLite comparison."""

import sqlite3
from collections.abc import Iterator
from pathlib import Path
from time import perf_counter

from docs.research.extraction.sqlite_baseline import load_batch

INITIAL = [("1", "Film A"), ("2", "Film B")]
CORRECTED = [("1", "Changed"), ("2", "Film B")]


def broken_rows() -> Iterator[tuple[str, str]]:
    yield CORRECTED[0]
    raise RuntimeError("injected source failure")


def snapshot(path: Path) -> list[tuple[str, str]]:
    with sqlite3.connect(path) as db:
        return db.execute("SELECT id, title FROM observation ORDER BY id").fetchall()


def run_sqlite(root: Path) -> None:
    path = root / "stdlib.sqlite3"
    started = perf_counter()
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE observation (id TEXT PRIMARY KEY, title TEXT NOT NULL)")
        load_batch(db, INITIAL)
        before = db.total_changes
        load_batch(db, INITIAL)
        unchanged_writes = db.total_changes - before
        assert unchanged_writes == 0
        try:
            load_batch(db, broken_rows())
        except RuntimeError as error:
            assert str(error) == "injected source failure"
        assert snapshot(path) == INITIAL
        load_batch(db, CORRECTED)
    assert snapshot(path) == CORRECTED
    print(
        "sqlite",
        "unchanged_writes",
        unchanged_writes,
        "seconds",
        round(perf_counter() - started, 3),
    )
