"""Atomic curated observations and reviewed crosswalks in the existing schema."""

from film_iq.ingest.curated_identity import record_identity
from film_iq.ingest.persist import _savepoint, persist
from film_iq.ingest.persist_checks import _key
from film_iq.recognition.models import Selection
from film_iq.recognition.storage import declare_selection


def persist_curated(db, captured, rows, manifest, accessed_at):
    with _savepoint(db):
        list_id = _key(manifest.policy.id, manifest.edition)
        _check_scope(db, list_id, manifest.ballot_scope)
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
            declare_selection(
                db,
                entry,
                revision,
                Selection(manifest.evidence_kind, manifest.ballot_scope, manifest.edition),
            )
        db.execute(
            "UPDATE published_list SET author=? WHERE id=? AND author IS NULL",
            (manifest.ballot_scope, list_id),
        )
    return revision


def _check_scope(db, list_id, scope):
    """An edition key belongs to one ballot; correction cannot reattribute its history."""
    stored = db.execute("SELECT author FROM published_list WHERE id=?", (list_id,)).fetchone()
    if stored is not None and stored[0] != scope:
        raise ValueError("ballot scope differs from existing edition; use a distinct edition key")
