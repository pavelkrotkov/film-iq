"""Map the private Movary snapshot to the current YouTrack user.

This does not write Movary, tracker fields, or editable personal preferences.
It imports only through the YouTrack app's current-user endpoint. Before the
local import, live fictional single-user and anonymous-denial checks passed.
"""

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime
from typing import Any

from youtrack_client import ROOT, YouTrackClient, YouTrackError
from youtrack_enrich import custom_value

SIDECAR = ROOT / ".cache/tracker-poc/private/movary-watched.json"
INPUT = ROOT / ".cache/tracker-poc/private/film-input.json"


def check_same_observation(previous: dict[str, Any], proposed: dict[str, Any]) -> None:
    """Prevent a same-observation format upgrade from changing visible events."""
    if previous.get("status") == "unknown":
        return
    if previous.get("status") != "available" or not isinstance(previous.get("films"), dict):
        raise YouTrackError("Existing watched snapshot is unavailable")
    try:
        old_time = datetime.fromisoformat(previous["observed_at"].replace("Z", "+00:00"))
        new_time = datetime.fromisoformat(proposed["observed_at"].replace("Z", "+00:00"))
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        raise YouTrackError("Watched snapshot observation time is invalid") from exc
    if old_time == new_time:

        def without_identity(films: dict[str, Any]) -> dict[str, Any]:
            if any(not isinstance(film, dict) for film in films.values()):
                raise YouTrackError("Existing watched snapshot is malformed")
            return {
                key: {k: v for k, v in film.items() if k != "tmdb_id"}
                for key, film in films.items()
            }

        if without_identity(previous["films"]) != without_identity(proposed["films"]):
            raise YouTrackError("Same-observation watched mapping differs; review before replacing")
        if any(
            "tmdb_id" in old and old["tmdb_id"] != proposed["films"][key].get("tmdb_id")
            for key, old in previous["films"].items()
        ):
            raise YouTrackError(
                "Same-observation watched identity differs; review before replacing"
            )


def prepare(
    sidecar: dict[str, Any],
    source: dict[str, Any],
    issues: list[dict[str, Any]],
    previous: dict[str, Any],
) -> dict[str, Any]:
    users = sidecar.get("users")
    if not isinstance(users, dict) or len(users) != 1:
        raise ValueError("Expected exactly one private source mapping")
    snapshot = next(iter(users.values()))
    if snapshot.get("source") != "Movary" or snapshot.get("unresolved_history") != []:
        raise ValueError("Movary snapshot source or completeness is uncertain")
    observed = snapshot.get("observed_at")
    watched = snapshot.get("films")
    if not isinstance(observed, str) or not isinstance(watched, dict):
        raise ValueError("Movary snapshot is invalid")
    provenance = source.get("provenance")
    if (
        not isinstance(provenance, dict)
        or provenance.get("movary_refresh_complete") is not True
        or provenance.get("movary_refresh") != observed
    ):
        raise ValueError("Movary snapshot is stale or its refresh is incomplete")
    films = source.get("films")
    if not isinstance(films, list):
        raise ValueError("Private source manifest is invalid")
    watched_ids = [film.get("tmdb_id") for film in films if film.get("watched") is True]
    if any(type(ident) is not int or not 0 < ident <= 2147483647 for ident in watched_ids):
        raise ValueError("Watched film identity is invalid")
    if len(set(watched_ids)) != len(watched_ids):
        raise ValueError("Duplicate watched film identity")
    expected = {str(ident) for ident in watched_ids}
    if set(watched) != expected:
        raise ValueError("Movary snapshot and current manifest disagree")
    if previous.get("status") != "available" or not isinstance(previous.get("films"), dict):
        raise YouTrackError("Existing watched snapshot is unavailable")
    try:
        old_time = datetime.fromisoformat(previous["observed_at"].replace("Z", "+00:00"))
        source_time = datetime.fromisoformat(observed.replace("Z", "+00:00"))
        if (
            old_time.utcoffset() is None
            or source_time.utcoffset() is None
            or old_time != source_time
        ):
            raise ValueError("Snapshot observations differ")
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        raise YouTrackError("Watched snapshot observations differ or are invalid") from exc
    lookup: dict[str, int | None] = {}
    seen_ids: set[int] = set()
    for issue in issues:
        readable = issue.get("idReadable")
        if (
            not isinstance(readable, str)
            or not readable.startswith("FILMREAL-")
            or readable in lookup
        ):
            raise YouTrackError("Unexpected or duplicate YouTrack project record")
        key = custom_value(issue, "FilmIQ TMDB ID")
        if key is not None and (
            type(key) is not int or not 0 < key <= 2147483647 or key in seen_ids
        ):
            raise YouTrackError("YouTrack film identity is invalid or duplicated")
        lookup[readable] = key
        if key is not None:
            seen_ids.add(key)

    def fingerprint(entry: Any) -> str:
        if (
            not isinstance(entry, dict)
            or entry.get("watched") is not True
            or not isinstance(entry.get("played_watch_dates"), list)
            or not isinstance(entry.get("history_export_dates"), list)
        ):
            raise ValueError("Invalid watched event")
        return json.dumps(
            [entry["watched"], entry["played_watch_dates"], entry["history_export_dates"]],
            sort_keys=True,
            separators=(",", ":"),
        )

    by_fingerprint: dict[str, list[str]] = defaultdict(list)
    for key, entry in watched.items():
        by_fingerprint[fingerprint(entry)].append(key)
    old_films = previous["films"]
    if not set(old_films).issubset(lookup):
        raise YouTrackError("Some prior watched issues are unavailable")
    counts = Counter(fingerprint(entry) for entry in old_films.values())
    source_counts = Counter({key: len(values) for key, values in by_fingerprint.items()})
    if counts != source_counts:
        raise YouTrackError("Watched event multisets differ; migration stopped")
    migrated = {}
    for issue, entry in old_films.items():
        fp = fingerprint(entry)
        matches = by_fingerprint.get(fp, [])
        ident = int(matches[0]) if len(matches) == 1 and counts[fp] == 1 else None
        if ident != lookup[issue]:
            ident = None
        migrated[issue] = {**entry, "tmdb_id": ident}
    result = {
        "version": "youtrack-poc-movary-watched-v2",
        "project": "FILMREAL",
        "source": "Movary",
        "complete": True,
        "observed_at": observed,
        "films": migrated,
    }
    check_same_observation(previous, result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    sidecar = json.loads(SIDECAR.read_text(encoding="utf-8"))
    source = json.loads(INPUT.read_text(encoding="utf-8"))
    client = YouTrackClient()
    me = client.request("users/me", query={"fields": "id,login"})
    if me.get("login") != "admin":
        raise YouTrackError("The token does not identify the POC administrator")
    issues = client.pages(
        "issues",
        query={
            "fields": "id,idReadable,customFields(name,value)",
            "query": "project: {FILMREAL} sort by: {issue id} asc",
        },
    )
    previous = client.request(
        "extensionEndpoints/filmiq-poc/movary/watched", query={"project": "FILMREAL"}
    )
    if not isinstance(previous, dict):
        raise YouTrackError("Existing watched snapshot is unavailable")
    payload = prepare(sidecar, source, issues, previous)
    if not args.apply:
        bound = sum(entry["tmdb_id"] is not None for entry in payload["films"].values())
        print(f"Prepared {len(payload['films'])} watched entries: {bound} bound; no changes made")
        return
    result = client.request("extensionEndpoints/filmiq-poc/movary/import", body=payload)
    if result.get("status") != "imported" or result.get("films") != len(payload["films"]):
        raise YouTrackError("Watched snapshot import was not confirmed")
    print(f"Imported {len(payload['films'])} watched mappings for the current user")


if __name__ == "__main__":
    main()
