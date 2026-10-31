"""Read-only first-use discovery report with separate source and personal judgments."""

from film_iq.discovery_cohort import validate_cohort
from film_iq.discovery_evidence import accepted_row, recognition
from film_iq.discovery_personal import fresh_snapshot, personal_index
from film_iq.recognition.discovery import attach_components

SOURCE_FIELDS = (
    "source_id",
    "source_url",
    "edition",
    "ballot_scope",
    "position",
    "rank",
    "tie",
    "published_at",
    "eligibility_date",
    "raw_title",
    "director",
    "year",
    "locator",
)


def _candidate(row, accepted, personal, scores, snapshot_available):
    facts, tmdb = accepted if accepted is not None else (row, row["tmdb_id"])
    state = personal.get(tmdb, {})
    watched = state.get("watched", False) if snapshot_available and tmdb else None
    return {
        **{key: facts[key] for key in SOURCE_FIELDS},
        "entry_id": facts.get("entry_id"),
        "revision_id": facts.get("revision_id"),
        "evidence_kind": facts.get("evidence_kind", "unknown"),
        "source_completeness": facts.get("accepted_completeness"),
        "source_lineage_kind": facts.get("accepted_lineage_kind"),
        "source_lineage": facts.get("accepted_lineage"),
        "source_eligibility": facts.get("accepted_eligibility"),
        "tmdb_id": tmdb,
        "identity_status": "reviewed" if accepted is not None and tmdb else "unresolved",
        "extraction_status": "accepted" if accepted is not None else "pending_review",
        "watched": watched,
        "watched_dates": state.get("watched_dates", []),
        "personal_enjoyment": state.get("personal_enjoyment"),
        "personal_artistic_merit": state.get("personal_artistic_merit"),
        "merit_status": state.get("merit_status", "unknown"),
        "external_critical_recognition": scores.get(tmdb),
        "access": "unknown; price, entitlement and freshness unverified",
    }


def build_discovery(cohort: dict, snapshot: dict | None = None, *, db=None, refresh_status=None):
    """Only current accepted, reviewed, freshly unwatched films enter suggestions."""
    personal, scores = personal_index(snapshot), recognition(db)
    stale = not fresh_snapshot(snapshot, refresh_status)
    candidates = [
        _candidate(
            row,
            accepted_row(db, cohort["revision_id"], row["position"]),
            personal,
            scores,
            snapshot is not None,
        )
        for row in validate_cohort(cohort, db)
    ]
    candidates = attach_components(candidates, db)
    suggestions = [row for row in candidates if _suggested(row, stale)]
    return {
        "mode": "read-only discovery",
        "last_successful_refresh": snapshot["last_successful_refresh"] if snapshot else None,
        "personal_state_stale": stale,
        "completeness": cohort["completeness"],
        "lineage": cohort["lineage"],
        "total_candidates": len(candidates),
        **_counts(candidates),
        "candidates": candidates,
        "suggested_unwatched": suggestions,
        "options": ["No purchase / no new service; rental and streaming options remain unknown"],
    }


def _suggested(row: dict, stale: bool) -> bool:
    return (
        not stale
        and row["extraction_status"] == "accepted"
        and row["identity_status"] == "reviewed"
        and row["watched"] is False
    )


def _counts(candidates):
    return {
        "accepted": sum(row["extraction_status"] == "accepted" for row in candidates),
        "unresolved": sum(row["identity_status"] != "reviewed" for row in candidates),
        "watched_excluded": sum(row["watched"] is True for row in candidates),
    }
