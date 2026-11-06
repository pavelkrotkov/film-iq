"""Preview or create neutral film records for the two observed watchlist entries.

This local-only tool never changes Movary, preferences, the watchlist property,
or existing issues and never contacts a provider. Review the owner-only preview
before using --apply. Run a single writer; YouTrack has no unique-ID constraint.
"""

import argparse
import hashlib
import json
import os
import unicodedata
from pathlib import Path
from urllib.parse import quote

from kaneo_watched_refresh import private_existing
from movary_watchlist_projection import project as project_watchlist
from tmdb_cache_batch import identities
from youtrack_client import YouTrackClient, YouTrackError
from youtrack_enrich import custom_value
from youtrack_private_import import issue_body
from youtrack_setup import project_id
from youtrack_watched_property_backup import private_path
from youtrack_watchlist_import import ENDPOINT, current

PROJECT = "FILMREAL"
FIELDS = "id,idReadable,summary,project(id,shortName),customFields(name,value(name,text))"
VERSION = "youtrack-watchlist-film-preview-v1"


def digest(value) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def title_key(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def issues(client, expected_project_id):
    rows = client.pages(
        "issues", query={"fields": FIELDS, "query": "project: {FILMREAL} sort by: {issue id} asc"}
    )
    ids, issue_ids = set(), set()
    for row in rows:
        if (
            not isinstance(row, dict)
            or not isinstance(row.get("id"), str)
            or not isinstance(row.get("idReadable"), str)
            or not row["idReadable"].startswith(PROJECT + "-")
            or row.get("project", {}).get("shortName") != PROJECT
            or row.get("project", {}).get("id") != expected_project_id
            or row["idReadable"] in issue_ids
            or not isinstance(row.get("summary"), str)
            or not row["summary"].strip()
        ):
            raise ValueError("Project issue listing is invalid")
        issue_ids.add(row["idReadable"])
        ident = custom_value(row, "FilmIQ TMDB ID")
        if ident is not None:
            if type(ident) is not int or not 0 < ident <= 2147483647 or ident in ids:
                raise ValueError("Project film IDs are invalid or duplicated")
            ids.add(ident)
    return rows


def plan(client, snapshot, status, approved_ids, snapshot_digest, status_digest):
    projection = project_watchlist(snapshot, status, [])
    if len(projection["entries"]) != 2:
        raise ValueError("Expected exactly the two observed watchlist entries")
    prop = current(client)
    view = client.request(ENDPOINT + "list", query={"project": PROJECT})
    expected = {
        "status": "available",
        "source": "Movary",
        "observed_at": projection["observed_at"],
        "entries": projection["entries"],
    }
    if view != expected:
        raise ValueError("Current user's watchlist differs from the source observation")
    project = project_id(client, PROJECT)
    rows = issues(client, project)
    by_id = {custom_value(row, "FilmIQ TMDB ID"): row for row in rows}
    pending, existing, conflicts = [], 0, 0
    for entry in projection["entries"]:
        ident, title = entry["tmdb_id"], entry["title"]
        if not isinstance(title, str) or not title.strip():
            conflicts += 1
            continue
        current_issue = by_id.get(ident)
        if current_issue:
            if title_key(current_issue["summary"]) != title_key(title):
                conflicts += 1
            else:
                existing += 1
            continue
        if ident in approved_ids or any(
            title_key(row["summary"]) == title_key(title) for row in rows
        ):
            conflicts += 1
            continue
        pending.append({"tmdb_id": ident, "title": title})
    if len({title_key(entry["title"]) for entry in pending}) != len(pending):
        conflicts += 1
    return {
        "version": VERSION,
        "project_id": project,
        "snapshot_sha256": snapshot_digest,
        "status_sha256": status_digest,
        "watchlist_sha256": digest(prop),
        "provider_approval_sha256": digest(sorted(approved_ids)),
        "issues_sha256": digest(rows),
        "pending": pending,
        "existing": existing,
        "conflicts": conflicts,
    }


def neutral_body(entry, project):
    return issue_body(
        {
            "tmdb_id": entry["tmdb_id"],
            "title": entry["title"],
            "source_year": None,
            "director": None,
            "accepted_discovery_evidence": None,
            "field_provenance": {
                "tmdb_id": "Movary API or native export; not independently reverified here",
                "title": "Movary API or native export; upstream catalog origin is unknown",
            },
        },
        project,
    )


def apply(client, reviewed, load_current):
    if reviewed.get("version") != VERSION or reviewed.get("conflicts"):
        raise ValueError("Reviewed preview contains conflicts")
    if load_current() != reviewed:
        raise ValueError("Source, approval or project changed since preview")
    created = 0
    fixed_keys = (
        "version",
        "project_id",
        "snapshot_sha256",
        "status_sha256",
        "watchlist_sha256",
        "provider_approval_sha256",
    )
    for entry in reviewed["pending"]:
        # Recheck all other targets before each write. A lost response stops the
        # run; it never automatically retries an uncertain creation.
        current_plan = load_current()
        if (
            any(current_plan[key] != reviewed[key] for key in fixed_keys)
            or current_plan["conflicts"]
            or current_plan["pending"] != reviewed["pending"][created:]
            or current_plan["existing"] != reviewed["existing"] + created
        ):
            raise ValueError("Film identity or title changed; inspect before retrying")
        try:
            result = client.request(
                "issues",
                query={"fields": "id,idReadable"},
                body=neutral_body(entry, reviewed["project_id"]),
            )
            if not isinstance(result, dict) or not isinstance(result.get("id"), str):
                raise ValueError("Missing issue ID")
            row = client.request("issues/" + quote(result["id"], safe=""), query={"fields": FIELDS})
            if (
                row.get("project", {}).get("shortName") != PROJECT
                or row.get("summary") != entry["title"]
                or custom_value(row, "FilmIQ TMDB ID") != entry["tmdb_id"]
                or custom_value(row, "FilmIQ Lifecycle").get("name") != "Discovery"
            ):
                raise ValueError("Created record readback differs")
        except (YouTrackError, ValueError, TypeError, KeyError, AttributeError):
            raise RuntimeError("Creation outcome unconfirmed; inspect before retrying") from None
        created += 1
    return {"status": "applied", "created": created}


def write_preview(path: Path, value: dict) -> None:
    path = private_path(path, existing=False)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as output:
        json.dump(value, output, ensure_ascii=False, sort_keys=True)
        output.write("\n")
        output.flush()
        os.fsync(output.fileno())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--preview", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    snapshot = private_existing(args.snapshot)
    status = private_existing(snapshot.with_suffix(snapshot.suffix + ".status"))
    client = YouTrackClient()

    def load_current():
        source_bytes, status_bytes = snapshot.read_bytes(), status.read_bytes()
        return plan(
            client,
            json.loads(source_bytes),
            json.loads(status_bytes),
            identities(),
            hashlib.sha256(source_bytes).hexdigest(),
            hashlib.sha256(status_bytes).hexdigest(),
        )

    if args.apply:
        reviewed = json.loads(private_path(args.preview, existing=True).read_text())
        print(json.dumps(apply(client, reviewed, load_current)))
    else:
        result = load_current()
        write_preview(args.preview, result)
        print(
            json.dumps(
                {
                    "status": "preview",
                    "pending": len(result["pending"]),
                    "existing": result["existing"],
                    "conflicts": result["conflicts"],
                }
            )
        )


if __name__ == "__main__":
    main()
