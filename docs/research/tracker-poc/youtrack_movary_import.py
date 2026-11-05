"""Map the private Movary snapshot to the current YouTrack user.

This does not write Movary, tracker fields, or editable personal preferences.
It imports only through the YouTrack app's current-user endpoint. Before the
local import, live fictional single-user and anonymous-denial checks passed.
"""

import argparse
import json
from typing import Any

from youtrack_client import ROOT, YouTrackClient, YouTrackError
from youtrack_enrich import custom_value

SIDECAR = ROOT / ".cache/tracker-poc/private/movary-watched.json"
INPUT = ROOT / ".cache/tracker-poc/private/film-input.json"


def prepare(
    sidecar: dict[str, Any], source: dict[str, Any], issues: list[dict[str, Any]]
) -> dict[str, Any]:
    users = sidecar.get("users")
    if not isinstance(users, dict) or len(users) != 1:
        raise ValueError("Expected exactly one private source mapping")
    snapshot = next(iter(users.values()))
    if snapshot.get("source") != "Movary" or snapshot.get("unresolved_history"):
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
    expected = {str(film["tmdb_id"]) for film in films if film.get("watched") is True}
    if set(watched) != expected:
        raise ValueError("Movary snapshot and current manifest disagree")
    lookup: dict[str, str] = {}
    for issue in issues:
        key = custom_value(issue, "FilmIQ TMDB ID")
        if key is None:
            continue
        if type(key) is not int or str(key) in lookup:
            raise YouTrackError("YouTrack film identity is invalid or duplicated")
        readable = issue.get("idReadable")
        if not isinstance(readable, str) or not readable.startswith("FILMREAL-"):
            raise YouTrackError("Unexpected YouTrack project record")
        lookup[str(key)] = readable
    if not expected.issubset(lookup):
        raise YouTrackError("Some watched films have no canonical YouTrack issue")
    return {
        "version": "youtrack-poc-movary-watched-v1",
        "project": "FILMREAL",
        "source": "Movary",
        "complete": True,
        "observed_at": observed,
        "films": {lookup[key]: watched[key] for key in watched},
    }


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
    payload = prepare(sidecar, source, issues)
    if not args.apply:
        print(f"Prepared {len(payload['films'])} watched mappings; no changes made")
        return
    result = client.request("extensionEndpoints/filmiq-poc/movary/import", body=payload)
    if result.get("status") != "imported" or result.get("films") != len(payload["films"]):
        raise YouTrackError("Watched snapshot import was not confirmed")
    print(f"Imported {len(payload['films'])} watched mappings for the current user")


if __name__ == "__main__":
    main()
