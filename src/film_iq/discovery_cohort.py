"""Require complete current accepted selections, not self-declared subset counts."""


def validate_cohort(cohort: dict, db=None) -> list[dict]:
    rows = cohort["candidates"]
    if not isinstance(rows, list) or len(rows) != cohort["total_candidates"]:
        raise ValueError("cohort count must match all supplied candidates")
    positions = [row["position"] for row in rows]
    if len(positions) != len(set(positions)):
        raise ValueError("cohort positions must be unique")
    _complete_revision(db, cohort["revision_id"], positions)
    return rows


def _complete_revision(db, revision, positions):
    if (
        db is None
        or db.execute(
            "SELECT 1 FROM current_extraction WHERE revision_id=?", (revision,)
        ).fetchone()
        is None
    ):
        return
    expected = {
        row[0]
        for row in db.execute(
            "SELECT position FROM entry_observation WHERE revision_id=?", (revision,)
        )
    }
    if set(positions) != expected:
        raise ValueError("cohort must contain the complete current accepted revision")
