"""Record each permitted local import separately from its idempotent evidence."""

from datetime import UTC, datetime

from film_iq.ingest.acquisition import begin_attempt, finish_attempt
from film_iq.ingest.acquisition_policy import set_permission
from film_iq.ingest.curated import import_list

METHOD = "manual-curated-csv"


def persist_attempt(db, body, manifest, started_at):
    """Commit acquisition intent before import; failed imports never advance cursors."""
    _permission(db, manifest, started_at)
    attempt = begin_attempt(db, manifest.policy.id, started_at)
    try:
        with db:
            result = import_list(body, manifest, db=db, accessed_at=started_at)
    except Exception:
        finish_attempt(db, attempt, _now(), "error", error_code="curated_persist_failed")
        raise
    finish_attempt(
        db,
        attempt,
        _now(),
        "success",
        revision_id=result["revision_id"],
        cursor=result["revision_id"],
    )
    return result


def _permission(db, manifest, reviewed_at):
    row = db.execute(
        "SELECT method FROM acquisition_permission WHERE source_id=?", (manifest.policy.id,)
    ).fetchone()
    if row is None:
        with db:
            set_permission(
                db,
                manifest.policy,
                method=METHOD,
                decision=manifest.rights_status,
                evidence=manifest.rights_evidence,
                reviewed_at=reviewed_at,
            )
    elif row[0] != METHOD:
        raise PermissionError("existing permission does not authorize manual-curated-csv")


def _now():
    return datetime.now(UTC).isoformat()
