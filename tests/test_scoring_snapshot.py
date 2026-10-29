import sqlite3
from datetime import date

import pytest

from film_iq.scoring import Evidence, score
from film_iq.scoring.snapshot import initialize, replay, save


def entry(film: str, list_id: str, group: str, rank: int | None, **kwargs) -> Evidence:
    return Evidence(
        film,
        list_id,
        f"https://example.org/{list_id}",
        date(2024, 12, 1),
        group,
        "2024 releases",
        rank,
        **kwargs,
    )


def test_snapshot_roundtrip_and_version_guard(tmp_path) -> None:
    path = tmp_path / "scores.db"
    evidence = [
        entry("a", "original", "critic", 2),
        entry("a", "unranked", "other", None),
        entry("a", "aggregate", "aggregate", 1, derivative_of=("original",)),
        entry("b", "original", "critic", 2),
    ]
    with sqlite3.connect(path) as db:
        initialize(db)
        snapshot_id = save(db, evidence, "2026-01-01T00:00:00Z")
        assert save(db, list(reversed(evidence)) + evidence[:1], "later") == snapshot_id
        assert db.execute("SELECT count(*), created_at FROM scoring_snapshot").fetchone() == (
            1,
            "2026-01-01T00:00:00Z",
        )
    with sqlite3.connect(path) as db:
        assert replay(db, snapshot_id) == score(evidence)
        db.execute("UPDATE scoring_snapshot SET version = 'unknown'")
        with pytest.raises(ValueError, match="unsupported scoring version"):
            replay(db, snapshot_id)
        with pytest.raises(KeyError):
            replay(db, "missing")


def test_snapshot_preserves_unknown_date_and_observation_provenance() -> None:
    unknown = Evidence(
        "a",
        "list",
        "https://example.org/list",
        None,
        "critic",
        "eligible",
        1,
        entry_id="entry",
        revision_id="revision",
        match_decision_id="match",
    )
    dated = Evidence(
        "a",
        "list",
        "https://example.org/list",
        date(2024, 1, 1),
        "critic",
        "eligible",
        1,
        entry_id="entry2",
        revision_id="revision",
        match_decision_id="match2",
    )
    with sqlite3.connect(":memory:") as db:
        initialize(db)
        snapshot_id = save(db, [unknown, dated], "now")
        assert replay(db, snapshot_id) == score([dated, unknown])
        assert replay(db, snapshot_id)[0].contributing == (unknown,)
        assert replay(db, snapshot_id)[0].excluded == (dated,)
