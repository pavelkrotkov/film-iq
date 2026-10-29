import sqlite3

import pytest

from film_iq.domain import Observation
from film_iq.storage import connect, migrate


@pytest.fixture
def evidence_db(tmp_path):
    db = connect(tmp_path / "evidence.db")
    migrate(db)
    migrate(db)
    assert db.execute("PRAGMA user_version").fetchone() == (8,)
    assert db.execute("PRAGMA foreign_keys").fetchone() == (1,)
    assert db.execute("PRAGMA journal_mode").fetchone() == ("wal",)
    db.execute(
        "INSERT INTO source (id, name, family, independence_group, url, country, cadence, access_policy, retention_policy, redistribution_policy, attribution, health) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "s",
            "Source",
            "poll",
            "original",
            "https://example.test",
            None,
            None,
            "public",
            "metadata only",
            "no copies",
            "cite source",
            None,
        ),
    )
    db.execute(
        "INSERT INTO source_run VALUES (?,?,?,?,?,?,?,?)",
        (
            "run",
            "s",
            "2026-01-01Z",
            None,
            "success",
            "v1",
            None,
            None,
        ),
    )
    db.execute(
        "INSERT INTO source_document VALUES (?,?,?,?,?,?,?,?)",
        (
            "doc",
            "s",
            "https://example.test/list",
            "hash",
            "2026-01-01Z",
            None,
            "success",
            "metadata only",
        ),
    )
    db.execute(
        "INSERT INTO published_list (id, source_id, edition, author, eligibility, period, rank_semantics, completeness, lineage) VALUES (?,?,?,?,?,?,?,?,?)",
        (
            "list",
            "s",
            "2025",
            "Critic",
            "released in 2025",
            "2025",
            "ranked",
            "partial",
            "original",
        ),
    )
    db.execute(
        "INSERT INTO extraction_revision VALUES (?,?,?,?,?,?,?,?)",
        (
            "rev",
            "s",
            "list",
            "doc",
            "run",
            "v1",
            "valid",
            "accepted",
        ),
    )
    db.execute("INSERT INTO list_entry VALUES (?,?,?,?)", ("entry", "s", "list", "item-1"))
    observation = Observation(
        "s",
        "list",
        "entry",
        "run",
        "rev",
        "Unchanged title",
        "context",
        "#1",
        1,
        "tie-a",
        raw_imdb_id="tt0000001",
        raw_tmdb_id="001",
    )
    values = (
        observation.entry_id,
        observation.source_id,
        observation.edition_id,
        observation.revision_id,
        observation.raw_title,
        observation.raw_context,
        None,
        None,
        None,
        1,
        observation.rank,
        observation.tie,
        observation.locator,
        "accepted",
        observation.raw_imdb_id,
        observation.raw_tmdb_id,
    )
    db.execute("INSERT INTO entry_observation VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", values)
    with pytest.raises(sqlite3.IntegrityError):
        db.execute("INSERT INTO entry_observation VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", values)
    with pytest.raises(sqlite3.IntegrityError):
        db.execute("INSERT INTO list_entry VALUES (?,?,?,?)", ("other", "s", "list", "item-1"))
    return db
