"""Create a private POC input from complete Movary and reviewed discovery outputs.

Only source-list facts and Movary identifiers/history are copied. TMDB display
metadata, personal ratings, notes and watchlist state are intentionally omitted.
"""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit

from review_links import attach_evidence

from film_iq.personal_io import private_json

REASON_FIELDS = (
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
    "entry_id",
    "revision_id",
    "evidence_kind",
    "source_completeness",
    "source_lineage_kind",
    "source_lineage",
    "source_eligibility",
)


def _identity(value: object) -> int:
    if type(value) is not int or value < 1:
        raise ValueError("A reviewed film is missing a valid TMDB identity")
    return value


def _reason(row: dict) -> dict:
    url = row.get("source_url")
    if not isinstance(url, str):
        raise ValueError("Evidence requires an HTTP(S) source URL")
    try:
        parsed = urlsplit(url)
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
        ):
            raise ValueError("Evidence requires a public HTTP(S) source URL")
    except ValueError:
        raise ValueError("Evidence requires a valid HTTP(S) source URL") from None
    return {key: row.get(key) for key in REASON_FIELDS}


def prepare(snapshot: dict, status: dict, report: dict) -> dict:
    """Require one complete refresh and join only trusted identities."""
    stamp = snapshot.get("last_successful_refresh")
    if (
        snapshot.get("version") != "movary-personal-v1"
        or not isinstance(stamp, str)
        or status.get("stale") is not False
        or status.get("last_successful_refresh") != stamp
        or report.get("personal_state_stale") is not False
        or report.get("last_successful_refresh") != stamp
    ):
        raise ValueError("Snapshot, refresh status and discovery must be current and match")
    if not all(
        isinstance(value, list)
        for value in (snapshot.get("films"), report.get("suggested_unwatched"))
    ):
        raise ValueError("Expected complete film and discovery lists")

    films: dict[int, dict] = {}
    for row in report["suggested_unwatched"]:
        tmdb_id = _identity(row.get("tmdb_id"))
        if (
            tmdb_id in films
            or row.get("identity_status") != "reviewed"
            or row.get("extraction_status") != "accepted"
            or row.get("watched") is not False
            or not isinstance(row.get("raw_title"), str)
            or not row["raw_title"].strip()
            or not isinstance(row.get("source_reasons"), list)
            or not row["source_reasons"]
        ):
            raise ValueError("Discovery has duplicate or unreviewed film entries")
        films[tmdb_id] = {
            "tmdb_id": tmdb_id,
            "title": row["raw_title"],
            "release_year": None,
            "source_year": row.get("year"),
            "director": row.get("director"),
            "field_provenance": {
                "tmdb_id": "reviewed accepted identity match",
                "title": "accepted source-list observation",
                "source_year": "source-listed year; not verified as release year",
                "director": "accepted source-list observation; may be unknown",
                "release_year": "unknown",
            },
            "origin": ["discovery"],
            "watched": False,
            "watched_dates": [],
            "source_reasons": [_reason(reason) for reason in row["source_reasons"]],
        }

    seen_watched: set[int] = set()
    for row in snapshot["films"]:
        if row.get("watched") is not True:
            continue
        tmdb_id = _identity(row.get("tmdb_id"))
        if tmdb_id in seen_watched:
            raise ValueError("Movary history contains duplicate TMDB identities")
        seen_watched.add(tmdb_id)
        dates = row.get("watched_dates")
        if not isinstance(dates, list) or any(
            not isinstance(d, str) and d is not None for d in dates
        ):
            raise ValueError("Movary watched dates must be strings or unknown")
        if tmdb_id in films:
            raise ValueError("Discovery unexpectedly contains a known watched film")
        films[tmdb_id] = {
            "tmdb_id": tmdb_id,
            "title": row.get("title"),
            "release_year": None,
            "source_year": None,
            "director": None,
            "field_provenance": {
                "tmdb_id": "Movary API or native export; not independently reverified here",
                "title": "Movary API or native export; upstream catalog origin is unknown",
                "source_year": "unknown",
                "director": "unknown",
                "release_year": "unknown",
            },
            "origin": ["movary_watched"],
            "watched": True,
            "watched_dates": dates,
            "source_reasons": [],
        }
    unresolved = snapshot.get("unresolved")
    if not isinstance(unresolved, dict) or not isinstance(unresolved.get("history"), list):
        raise ValueError("Missing unresolved Movary history")
    return {
        "version": "tracker-poc-private-film-input-v1",
        "prepared_at": datetime.now(UTC).isoformat(),
        "provenance": {
            "movary_refresh": stamp,
            "movary_refresh_complete": True,
            "discovery_completeness": report.get("completeness"),
            "discovery_cohort_count": report.get("cohort_count"),
            "discovery_ordering": report.get("ordering"),
            "source_note": "Source links are list evidence, not necessarily film reviews.",
            "retention_note": (
                "Private derived facts; original source permissions remain applicable. "
                "Movary title origin and retention terms are not established by this export."
            ),
        },
        "films": list(films.values()),
        "unresolved_history": [
            {key: row.get(key) for key in ("title", "year", "imdbId", "watchedAt")}
            for row in unresolved["history"]
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    snapshot = json.loads(args.snapshot.read_text())
    status = json.loads(args.snapshot.with_suffix(args.snapshot.suffix + ".status").read_text())
    report = json.loads(args.report.read_text())
    result = attach_evidence(prepare(snapshot, status, report), report)
    args.output.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    private_json(args.output, result)
    print(f"Prepared {len(result['films'])} private film records")


if __name__ == "__main__":
    main()
