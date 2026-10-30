"""Accepted source revision and replay stay semantically identical after restore."""

from film_iq.recovery import backup, restore
from film_iq.scoring import score
from film_iq.scoring.a1 import load_evidence
from film_iq.storage import connect, migrate


def test_restore_active_revision_replays_without_duplicate_votes(evidence_db, tmp_path):
    db = evidence_db
    db.execute("UPDATE source SET independence_verification='verified'")
    db.execute("UPDATE published_list SET lineage_kind='original', lineage_verification='verified'")
    db.execute("INSERT INTO film_index(id,tmdb_id) VALUES(42,123)")
    db.execute("INSERT INTO current_extraction(list_id,revision_id) VALUES('list','rev')")
    db.execute(
        "INSERT INTO match_decision VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
        ("m", "entry", "rev", 42, "[]", "synthetic", "1", None, None, "accepted", "now", None),
    )
    db.execute("INSERT INTO current_match(entry_id,revision_id,decision_id,film_id) VALUES('entry','rev','m',42)")
    db.commit()
    expected = score(load_evidence(db))
    backup(db, tmp_path / "accepted-backup.db")
    restore(tmp_path / "accepted-backup.db", tmp_path / "accepted-restored.db")
    recovered = connect(tmp_path / "accepted-restored.db")
    migrate(recovered)
    migrate(recovered)
    assert score(load_evidence(recovered)) == expected
    assert recovered.execute("SELECT count(*) FROM current_extraction").fetchone() == (1,)
    assert recovered.execute("SELECT count(*) FROM entry_observation").fetchone() == (1,)
    recovered.close()
