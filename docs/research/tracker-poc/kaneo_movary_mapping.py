"""Build a private per-user, source-tagged Movary watched-history sidecar.

This never changes Movary, tracker tasks, or editable preference records. The
sidecar is restricted to one existing project and is served only after the
preference bridge checks the requesting user's project access.
"""

import argparse
import http.cookiejar
import json
import urllib.request
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from kaneo_smoke import call

from film_iq.personal_io import private_json

VERSION = "tracker-poc-movary-watched-v1"


def _date(value: object) -> str | None:
    if value in (None, ""):
        return None
    if not isinstance(value, str):
        raise ValueError("invalid Movary watch date")
    try:
        date.fromisoformat(value)
    except ValueError:
        raise ValueError("invalid Movary watch date") from None
    return value


def mapping(snapshot: dict, status: dict) -> dict:
    stamp = snapshot.get("last_successful_refresh")
    if (
        snapshot.get("version") != "movary-personal-v1"
        or not isinstance(stamp, str)
        or status.get("stale") is not False
        or status.get("last_successful_refresh") != stamp
    ):
        raise ValueError("a complete, matching Movary refresh is required")
    if not isinstance(snapshot.get("films"), list):
        raise ValueError("missing complete Movary film list")
    films: dict[str, dict[str, Any]] = {}
    for row in snapshot["films"]:
        if row.get("watched") is not True:
            continue
        ident = row.get("tmdb_id")
        if type(ident) is not int or ident <= 0 or str(ident) in films:
            raise ValueError("invalid or duplicate watched identity")
        films[str(ident)] = {
            "watched": True,
            "played_watch_dates": [],
            "history_export_dates": [],
        }
    provenance = snapshot.get("provenance")
    if not isinstance(provenance, dict) or not isinstance(provenance.get("api"), dict):
        raise ValueError("missing Movary refresh provenance")
    played, history = provenance["api"].get("played"), provenance.get("history_csv")
    if not isinstance(played, list) or not isinstance(history, list):
        raise ValueError("missing complete played API or history export")
    seen = set()
    for row in played:
        ident = row["movie"]["ids"]["tmdb"]
        if type(ident) is not int or ident <= 0 or str(ident) not in films or ident in seen:
            raise ValueError("inconsistent played identity")
        seen.add(ident)
        events = row.get("watchDates")
        if not isinstance(events, list):
            raise ValueError("invalid played watch dates")
        for event in events:
            plays = event.get("plays")
            if type(plays) is not int or plays <= 0:
                raise ValueError("invalid Movary play count")
            films[str(ident)]["played_watch_dates"].append(
                {"date": _date(event.get("date")), "plays": plays}
            )
    unresolved = []
    for row in history:
        ident = row.get("tmdbId")
        watched_date = _date(row.get("watchedAt"))
        if not ident:
            unresolved.append(
                {
                    "title": row.get("title"),
                    "source_year": row.get("year"),
                    "imdb_id": row.get("imdbId"),
                    "date": watched_date,
                }
            )
        elif not isinstance(ident, str) or not ident.isdigit() or str(int(ident)) not in films:
            raise ValueError("history export has an unmatched watched identity")
        else:
            films[str(int(ident))]["history_export_dates"].append(watched_date)
    return {
        "source": "Movary",
        "observed_at": stamp,
        "films": films,
        "unresolved_history": unresolved,
    }


def merge(existing: dict | None, project: str, user: str, observation: dict) -> dict:
    if not project or not user:
        raise ValueError("project and user are required")
    if existing is None:
        existing = {"version": VERSION, "project_id": project, "users": {}}
    if (
        existing.get("version") != VERSION
        or existing.get("project_id") != project
        or not isinstance(existing.get("users"), dict)
    ):
        raise ValueError("sidecar belongs to a different project or version")
    prior = existing["users"].get(user)
    if prior is not None and (not isinstance(prior, dict) or prior.get("source") != "Movary"):
        raise ValueError("refusing to replace a different preference source")
    return {**existing, "users": {**existing["users"], user: observation}}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="http://localhost:15173")
    parser.add_argument("--directory", type=Path, required=True)
    args = parser.parse_args()
    parsed = urlsplit(args.base)
    if parsed.scheme != "http" or parsed.hostname not in ("localhost", "127.0.0.1"):
        raise ValueError("This experiment only supports a local loopback instance")
    directory, base = args.directory, args.base.rstrip("/")
    private = directory / "private"
    snapshot_file = private / "movary-snapshot.json"
    snapshot = json.loads(snapshot_file.read_text())
    status = json.loads(snapshot_file.with_suffix(".json.status").read_text())
    observation = mapping(snapshot, status)
    project = json.loads((private / "kaneo-private-ids.json").read_text())["project"]
    cookies = http.cookiejar.MozillaCookieJar(str(directory / "kaneo-cookies.txt"))
    cookies.load(ignore_discard=True)
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookies))
    session = call(opener, base, "/auth/get-session")
    user = session["user"]["id"]
    fields = call(opener, base, f"/custom-field/project/{project}")
    identities = [field for field in fields if field["name"] == "POC TMDB ID"]
    if len(identities) != 1:
        raise ValueError("private project identity field is missing or ambiguous")
    values = call(opener, base, f"/custom-field/project/{project}/values")
    ids = [row["value"] for row in values if row["fieldId"] == identities[0]["id"] and row["value"]]
    if len(ids) != len(set(ids)) or not set(observation["films"]).issubset(ids):
        raise ValueError("private project has missing or duplicate watched identities")
    target = private / "movary-watched.json"
    existing = json.loads(target.read_text()) if target.exists() else None
    result = merge(existing, project, user, observation)
    private_json(target, result)
    print(f"Mapped {len(observation['films'])} watched films for the authenticated POC user")


if __name__ == "__main__":
    main()
