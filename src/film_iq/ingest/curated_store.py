"""Atomic curated observations and reviewed crosswalks in the existing schema."""

from film_iq.ingest.curated_identity import record_identity
from film_iq.ingest.persist import _savepoint, persist
from film_iq.ingest.persist_checks import _key


def persist_curated(db, captured, rows, manifest, accessed_at):
    with _savepoint(db):
        revision = persist(db, captured, manifest.policy, manifest.edition, accessed_at)
        for row in rows:
            entry = _key(_key(manifest.policy.id, manifest.edition), str(row.position))
            db.execute(
                "UPDATE entry_observation SET director=?,listed_year=?,raw_tmdb_id=? "
                "WHERE entry_id=? AND revision_id=?",
                (
                    row.director,
                    row.year,
                    str(row.tmdb_id) if row.tmdb_id else None,
                    entry,
                    revision,
                ),
            )
            record_identity(db, entry, revision, row)
        db.execute(
            "UPDATE published_list SET author=? WHERE id=?",
            (manifest.ballot_scope, _key(manifest.policy.id, manifest.edition)),
        )
    return revision
