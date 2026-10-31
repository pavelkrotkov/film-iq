from dataclasses import replace
from pathlib import Path

import pytest

from film_iq.ingest.adapters import nbr_2023
from film_iq.ingest.persist import SourcePolicy, persist

FIXTURES = Path(__file__).parent / "fixtures/ingest"
POLICY = SourcePolicy(
    "nbr",
    "NBR",
    "https://nationalboardofreview.org/",
    "awards",
    "nbr",
    "public",
    "metadata",
    "none",
    "cite",
)


def test_invalid_entries_roll_back_entire_extraction(evidence_db):
    import sqlite3

    db = evidence_db
    result = nbr_2023.extract((FIXTURES / "nbr-2023.wiki").read_bytes())
    entry = result.entries[1]
    bad = replace(
        result, entries=(result.entries[0], replace(entry, title=""), *result.entries[2:])
    )
    with pytest.raises((ValueError, sqlite3.IntegrityError)):
        persist(db, bad, POLICY, "2023", "now")
    assert db.execute("SELECT count(*) FROM source WHERE id='nbr'").fetchone() == (0,)
