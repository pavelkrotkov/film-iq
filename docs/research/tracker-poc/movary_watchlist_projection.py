"""Preview a private, read-only Movary watchlist projection for tracker POCs.

This reads a completed local snapshot. It neither contacts Movary or providers
nor changes a tracker, a watchlist, or editable POC preferences.
"""

import argparse
import json
import os
import stat
from datetime import datetime
from pathlib import Path

from film_iq.personal_identity import api_movies
from film_iq.personal_io import private_json
from film_iq.personal_snapshot import VERSION


def validate_view(value: object) -> dict:
    """Validate a positive-only private snapshot before returning it to a user."""
    if (
        not isinstance(value, dict)
        or set(value) != {"version", "source", "observed_at", "entries"}
        or value.get("version") != "tracker-poc-movary-watchlist-v1"
        or value.get("source") != "Movary"
        or not isinstance(value.get("observed_at"), str)
        or not isinstance(value.get("entries"), list)
    ):
        raise ValueError("Invalid Movary watchlist snapshot")
    try:
        if datetime.fromisoformat(value["observed_at"]).utcoffset() is None:
            raise ValueError
        seen = set()
        for row in value["entries"]:
            if not isinstance(row, dict) or set(row) != {"tmdb_id", "title", "added_at"}:
                raise ValueError
            ident, title, added = row["tmdb_id"], row["title"], row["added_at"]
            if (
                type(ident) is not int
                or not 0 < ident <= 2147483647
                or ident in seen
                or (title is not None and (not isinstance(title, str) or not title.strip()))
                or (added is not None and (not isinstance(added, str) or not added))
            ):
                raise ValueError
            if added is not None:
                datetime.fromisoformat(added)
            seen.add(ident)
    except (TypeError, ValueError):
        raise ValueError("Invalid Movary watchlist snapshot") from None
    return value


def project(snapshot: dict, status: dict, existing_ids: list[int]) -> dict:
    """Retain positive source assertions and plan missing canonical films.

    An absent ID is deliberately not represented as an off-watchlist claim.
    The tracker IDs supplied here must come from one complete unique listing;
    a previously prepared input manifest is useful for preview only.
    """
    if not isinstance(snapshot, dict) or not isinstance(status, dict):
        raise ValueError("A complete Movary snapshot and status are required")
    stamp = snapshot.get("last_successful_refresh")
    if (
        snapshot.get("version") != VERSION
        or not isinstance(stamp, str)
        or status.get("stale") is not False
        or status.get("last_successful_refresh") != stamp
    ):
        raise ValueError("A complete matching Movary observation is required")
    try:
        if datetime.fromisoformat(stamp).utcoffset() is None:
            raise ValueError
    except ValueError:
        raise ValueError("Movary observation time must include a timezone") from None

    api = snapshot.get("provenance", {}).get("api")
    if not isinstance(api, dict) or not all(
        isinstance(api.get(name), list) for name in ("played", "history", "watchlist")
    ):
        raise ValueError("Complete Movary API collections are required")
    try:
        movies = api_movies({name: api[name] for name in ("played", "history", "watchlist")})
    except (KeyError, TypeError, ValueError):
        raise ValueError("Invalid Movary API crosswalk") from None
    films = snapshot.get("films")
    if not isinstance(films, list):
        raise ValueError("Complete Movary films are required")
    by_id = {}
    for film in films:
        if not isinstance(film, dict):
            raise ValueError("Invalid Movary film")
        ident = film.get("tmdb_id")
        if (
            type(ident) is not int
            or not 0 < ident <= 2147483647
            or ident in by_id
            or type(film.get("watchlist")) is not bool
        ):
            raise ValueError("Invalid or duplicate Movary film identity")
        by_id[ident] = film

    if (
        not isinstance(existing_ids, list)
        or any(type(value) is not int or not 0 < value <= 2147483647 for value in existing_ids)
        or len(set(existing_ids)) != len(existing_ids)
    ):
        raise ValueError("Existing tracker identities must be positive and unique")
    existing = set(existing_ids)
    entries, seen = [], set()
    for row in api["watchlist"]:
        try:
            movie = row["movie"]
            ident = movie["ids"]["tmdb"]
            source_id = movie["ids"]["movary"]
            added = row.get("addedAt")
        except (KeyError, TypeError):
            raise ValueError("Invalid Movary watchlist entry") from None
        if (
            type(ident) is not int
            or not 0 < ident <= 2147483647
            or ident in seen
            or type(source_id) is not int
            or source_id < 1
            or ident not in by_id
            or by_id[ident].get("movary_id") != source_id
            or by_id[ident]["watchlist"] is not True
            or movies.get(ident, {}).get("movary_id") != source_id
        ):
            raise ValueError("Movary watchlist identity is inconsistent or duplicated")
        if added is not None:
            if not isinstance(added, str) or not added:
                raise ValueError("Invalid Movary added-at value")
            try:
                datetime.fromisoformat(added)
            except ValueError:
                raise ValueError("Invalid Movary added-at value") from None
        seen.add(ident)
        title = by_id[ident].get("title")
        source_title = movie.get("title")
        # Do not silently select a title if the observation itself disagrees.
        usable_title = (
            title if isinstance(title, str) and title.strip() and title == source_title else None
        )
        entries.append({"tmdb_id": ident, "title": usable_title, "added_at": added})
    if {ident for ident, film in by_id.items() if film["watchlist"]} != seen:
        raise ValueError("Movary watchlist membership disagrees with source provenance")
    entries.sort(key=lambda item: item["tmdb_id"])
    view = {
        "version": "tracker-poc-movary-watchlist-v1",
        "source": "Movary",
        "observed_at": stamp,
        "entries": entries,
    }
    validate_view(view)
    return {
        **view,
        "missing_film_ids": [
            entry["tmdb_id"] for entry in entries if entry["tmdb_id"] not in existing
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--existing-manifest", type=Path, required=True)
    parser.add_argument("--private-preview", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    project_root = root.parent.parent if root.parent.name == ".worktrees" else root
    snapshot_file = args.snapshot.resolve(strict=True)
    manifest_file = args.existing_manifest.resolve(strict=True)
    if not snapshot_file.is_relative_to(project_root) or not manifest_file.is_relative_to(
        project_root
    ):
        raise ValueError("Inputs must remain inside the selected project")
    status_file = snapshot_file.with_suffix(snapshot_file.suffix + ".status").resolve(strict=True)
    for path in (snapshot_file, status_file, manifest_file):
        info = path.stat()
        if (
            not path.is_relative_to(project_root)
            or not stat.S_ISREG(info.st_mode)
            or info.st_uid != os.getuid()
            or info.st_mode & 0o077
        ):
            raise ValueError("Inputs must be owner-only project files")
    snapshot = json.loads(snapshot_file.read_text())
    status = json.loads(status_file.read_text())
    manifest = json.loads(manifest_file.read_text())
    if manifest.get("version") != "tracker-poc-private-film-input-v1" or not isinstance(
        manifest.get("films"), list
    ):
        raise ValueError("Unsupported existing input manifest")
    result = project(snapshot, status, [film.get("tmdb_id") for film in manifest["films"]])
    if args.private_preview:
        output = args.private_preview.resolve()
        parent = output.parent.stat()
        if (
            not output.is_relative_to(project_root)
            or output.exists()
            or not stat.S_ISDIR(parent.st_mode)
            or parent.st_uid != os.getuid()
            or parent.st_mode & 0o077
        ):
            raise ValueError("Preview must be a new file inside the selected project")
        private_json(output, result)
    print(
        json.dumps(
            {
                "status": "preview",
                "watchlisted": len(result["entries"]),
                "missing_from_input_manifest": len(result["missing_film_ids"]),
                "missing_titles": sum(item["title"] is None for item in result["entries"]),
            }
        )
    )


if __name__ == "__main__":
    main()
