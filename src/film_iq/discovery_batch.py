"""Join explicitly selected complete cohorts without duplicating suggested works."""

import json

from film_iq.discovery import build_discovery


def build_discoveries(cohorts, snapshot=None, *, db=None, refresh_status=None):
    """Keep every source observation; combine suggestions by reviewed work identity."""
    if not cohorts:
        raise ValueError("at least one complete cohort is required")
    revisions = [cohort["revision_id"] or json.dumps(cohort, sort_keys=True) for cohort in cohorts]
    if len(revisions) != len(set(revisions)):
        raise ValueError("duplicate cohort revision; supply each selection once")
    reports = [
        build_discovery(cohort, snapshot, db=db, refresh_status=refresh_status)
        for cohort in cohorts
    ]
    if len(reports) == 1:
        return reports[0]
    return _merge(cohorts, reports)


def _merge(cohorts, reports):
    candidates = [row for report in reports for row in report["candidates"]]
    suggestions = _suggestions(reports)
    return {
        **reports[0],
        "completeness": "intentionally_partial",
        "lineage": "Explicitly selected cohorts; each source retains its original lineage",
        "cohort_count": len(reports),
        "cohorts": [
            _coverage(cohort, report) for cohort, report in zip(cohorts, reports, strict=True)
        ],
        "total_candidates": len(candidates),
        "unique_films": _unique_films(candidates),
        **_totals(reports),
        "candidates": candidates,
        "suggested_unwatched": suggestions,
    }


def _unique_films(candidates):
    return len({row["tmdb_id"] for row in candidates if row["identity_status"] == "reviewed"})


def _totals(reports):
    return {
        key: sum(report[key] for report in reports)
        for key in ("accepted", "unresolved", "watched_excluded")
    }


def _suggestions(reports):
    works = {}
    for report in reports:
        for row in report["suggested_unwatched"]:
            work = works.setdefault(row["tmdb_id"], {**row, "source_reasons": []})
            work["source_reasons"].append(row)
    return list(works.values())


def _coverage(cohort, report):
    return {
        "revision_id": cohort["revision_id"],
        "completeness": cohort["completeness"],
        "lineage": cohort["lineage"],
        **{
            key: report[key]
            for key in ("total_candidates", "accepted", "unresolved", "watched_excluded")
        },
    }
