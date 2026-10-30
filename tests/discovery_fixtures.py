"""Synthetic report input, unrelated to any publisher or personal account."""

import json

from film_iq.personal_snapshot import VERSION


def cohort():
    return {
        "revision_id": "rev",
        "total_candidates": 1,
        "completeness": "intentionally_partial",
        "lineage": "synthetic original ballot",
        "candidates": [
            {
                "source_id": "s",
                "source_url": "https://example.test/list",
                "edition": "2025",
                "ballot_scope": "synthetic critic",
                "position": 1,
                "rank": 2,
                "tie": None,
                "published_at": None,
                "eligibility_date": None,
                "raw_title": "Synthetic Film",
                "director": None,
                "year": None,
                "locator": "#1",
                "tmdb_id": 123,
                "identity_status": "reviewed",
                "extraction_status": "accepted",
            }
        ],
    }


def snapshot(watched=False):
    return {
        "version": VERSION,
        "last_successful_refresh": "2026-10-30T00:00:00+00:00",
        "films": [
            {
                "tmdb_id": 123,
                "watched": watched,
                "watched_dates": [],
                "personal_enjoyment": 7,
                "personal_artistic_merit": None,
                "merit_status": "conflict",
            }
        ],
        "provenance": {"comments": "PRIVATE COMMENT NEVER IN REPORT"},
    }


def accept_source(db):
    db.execute(
        "UPDATE entry_observation SET raw_context=?,position=1,rank=2,tie=NULL",
        (json.dumps(cohort()["candidates"][0]),),
    )
    db.execute("INSERT INTO film_index(id,tmdb_id) VALUES(42,123)")
    db.execute(
        "INSERT INTO match_decision VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "m",
            "entry",
            "rev",
            42,
            "[]",
            "synthetic",
            "1",
            None,
            None,
            "accepted",
            "now",
            None,
        ),
    )
    db.execute(
        "INSERT INTO current_match(entry_id,revision_id,decision_id,film_id) VALUES('entry','rev','m',42)"
    )
    db.execute("INSERT INTO current_extraction(list_id,revision_id) VALUES('list','rev')")
