import sqlite3
from pathlib import Path

from film_iq.storage import migrate


def test_version_three_upgrade_keeps_lineage_unknown(tmp_path):
    db = sqlite3.connect(tmp_path / "v3.db")
    storage = Path(__file__).parents[1] / "src/film_iq/storage"
    for version in (1, 2, 3):
        db.executescript((storage / f"{version:03}.sql").read_text())
    db.execute(
        "INSERT INTO source (id, name, family, independence_group, url, access_policy, retention_policy, redistribution_policy, attribution) VALUES ('s', 's', 'poll', 'g', 'url', 'a', 'r', 'd', 'a')"
    )
    db.execute(
        "INSERT INTO published_list (id, source_id, edition, eligibility, rank_semantics, completeness, lineage, lineage_verification) VALUES ('l', 's', 'e', 'e', 'ranked', 'complete', 'derivative', 'verified')"
    )
    db.execute("PRAGMA user_version = 3")
    db.commit()
    migrate(db)
    assert db.execute(
        "SELECT lineage, lineage_verification, lineage_kind FROM published_list"
    ).fetchone() == ("derivative", "verified", "unknown")
    db.close()
