"""Preview or import one complete, local Movary watchlist observation.

This reads existing project-local files and the authenticated user's YouTrack
project; it does not access Movary, providers, tracker issues for writing, or
editable preferences. An owner-only property backup is required for apply.
"""

import argparse
import json
import os
from copy import deepcopy
from pathlib import Path
from typing import Any

from kaneo_watched_refresh import private_existing
from movary_watchlist_projection import project as project_watchlist
from youtrack_client import YouTrackClient
from youtrack_enrich import custom_value
from youtrack_watched_property_backup import private_path

ENDPOINT = "extensionEndpoints/filmiq-poc/movary-watchlist/"
VERSION = "filmiq-watchlist-property-export-v1"


def envelope(value: Any) -> dict:
    if (
        not isinstance(value, dict)
        or set(value) != {"version", "owner", "raw"}
        or value["version"] != VERSION
        or not isinstance(value["owner"], dict)
        or set(value["owner"]) != {"login", "ring_id"}
        or not all(isinstance(item, str) and item for item in value["owner"].values())
        or (value["raw"] is not None and not isinstance(value["raw"], str))
    ):
        raise ValueError("Watchlist property export is invalid")
    return value


def current(client: Any) -> dict:
    value = envelope(client.request(ENDPOINT + "property-export"))
    me = client.request("users/me", query={"fields": "id,login"})
    if not isinstance(me, dict) or me.get("login") != value["owner"]["login"]:
        raise ValueError("Watchlist owner does not match the API account")
    return value


def existing_ids(client: Any, project: str) -> list[int]:
    rows = client.pages(
        "issues",
        query={
            "fields": "id,idReadable,project(shortName),customFields(name,value)",
            "query": f"project: {{{project}}} sort by: {{issue id}} asc",
        },
    )
    ids, seen_issues = [], set()
    for issue in rows:
        if (
            not isinstance(issue, dict)
            or not isinstance(issue.get("id"), str)
            or issue["id"] in seen_issues
            or issue.get("project", {}).get("shortName") != project
        ):
            raise ValueError("Project listing is invalid or incomplete")
        seen_issues.add(issue["id"])
        ident = custom_value(issue, "FilmIQ TMDB ID")
        if ident is None:
            continue
        if type(ident) is not int or not 0 < ident <= 2147483647 or ident in ids:
            raise ValueError("Project film IDs are invalid or duplicated")
        ids.append(ident)
    return ids


def run(
    client: Any, snapshot: dict, status: dict, project: str, *, apply=False, backup=None
) -> dict:
    if project not in ("FILMREAL", "FILMPOC"):
        raise ValueError("Unexpected project")
    before = current(client)
    projection = project_watchlist(snapshot, status, existing_ids(client, project))
    proposed = {key: projection[key] for key in ("version", "source", "observed_at", "entries")}
    proposed["project"] = project
    counts = {
        "entries": len(proposed["entries"]),
        "missing_films": len(projection["missing_film_ids"]),
    }
    if not apply:
        return {"status": "preview", **counts}
    if backup is None:
        raise ValueError("An owner-only property backup path is required")
    target = private_path(backup, existing=False)
    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as output:
        json.dump(before, output, ensure_ascii=False)
        output.write("\n")
        output.flush()
        os.fsync(output.fileno())
    if json.loads(target.read_text()) != before:
        raise RuntimeError("Watchlist backup could not be verified")
    if current(client) != before:
        raise ValueError("Watchlist property changed; inspect before retrying")
    try:
        result = client.request(
            ENDPOINT + "import",
            body={"owner": before["owner"], "expected": before["raw"], "snapshot": proposed},
        )
        if (
            not isinstance(result, dict)
            or result.get("status") not in ("imported", "unchanged")
            or result.get("entries") != counts["entries"]
        ):
            raise ValueError("Unexpected import response")
        after = client.request(ENDPOINT + "list", query={"project": project})
        after_full = current(client)
    except Exception:
        raise RuntimeError("Import outcome unconfirmed; inspect before retrying") from None
    expected = {
        "status": "available",
        "source": "Movary",
        "observed_at": proposed["observed_at"],
        "entries": proposed["entries"],
    }
    if after != expected:
        raise RuntimeError("Watchlist readback differs; inspect before retrying")
    prior_state = (
        json.loads(before["raw"])
        if before["raw"]
        else {"version": "youtrack-poc-movary-watchlists-v1", "projects": {}}
    )
    expected_state = deepcopy(prior_state)
    projects = expected_state.get("projects") if isinstance(expected_state, dict) else None
    if not isinstance(projects, dict):
        raise RuntimeError("Watchlist property readback differs; inspect before retrying")
    projects[project] = proposed
    if (
        after_full["owner"] != before["owner"]
        or not after_full["raw"]
        or json.loads(after_full["raw"]) != expected_state
    ):
        raise RuntimeError("Watchlist property readback differs; inspect before retrying")
    return {"status": result["status"], **counts}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--project", choices=("FILMREAL", "FILMPOC"), default="FILMREAL")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--backup", type=Path)
    args = parser.parse_args()
    snapshot = private_existing(args.snapshot)
    status = private_existing(snapshot.with_suffix(snapshot.suffix + ".status"))
    result = run(
        YouTrackClient(),
        json.loads(snapshot.read_text()),
        json.loads(status.read_text()),
        args.project,
        apply=args.apply,
        backup=args.backup,
    )
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
