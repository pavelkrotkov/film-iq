import sqlite3
from pathlib import Path

import pytest

from film_iq.storage import migrate


def test_historical_v1_is_rejected_without_changes(tmp_path):
    db = sqlite3.connect(tmp_path / "historical.db")
    schema = Path(__file__).parent / "fixtures/001-historical-47a29d9.sql"
    db.executescript(schema.read_text() + "\nPRAGMA user_version = 1;")
    before = list(db.iterdump())
    with pytest.raises(ValueError, match="obsolete schema shape"):
        migrate(db)
    assert list(db.iterdump()) == before
    assert db.execute("PRAGMA user_version").fetchone() == (1,)
