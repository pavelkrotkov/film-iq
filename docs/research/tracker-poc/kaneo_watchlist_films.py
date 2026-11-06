"""Preview or create neutral Kaneo records for the two observed watchlist films.

Use only a separately issued bearer key and a single writer. This tool does not
contact Movary or a metadata provider, edit existing tasks, or modify preferences.
"""

import argparse
import hashlib
import json
import os
import sys
import unicodedata
from pathlib import Path
from urllib.parse import quote, urlsplit

from kaneo_direct_reviews import api_key_opener
from kaneo_private_import import PUBLIC_FIELD_PROVENANCE, PUBLIC_IDENTITY_PROVENANCE
from kaneo_smoke import call
from kaneo_watched_refresh import PRIVATE, private_existing
from movary_watchlist_projection import project as project_watchlist

VERSION = "kaneo-watchlist-film-preview-v1"
FIELD_NAMES = ("POC TMDB ID", "POC Identity Provenance", "POC Field Provenance")


def digest(value):
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def title_key(value):
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def inventory(request, project):
    """List all board buckets and validate pagination and identity-field values."""
    segment = quote(project, safe="")
    definitions = request(f"/custom-field/project/{segment}")
    if not isinstance(definitions, list):
        raise ValueError("Invalid field definitions")
    fields = {}
    for name in FIELD_NAMES:
        found = [row for row in definitions if row.get("name") == name]
        if len(found) != 1 or found[0].get("type") != "text":
            raise ValueError("Required field is missing or ambiguous")
        field_id = found[0].get("id")
        if not isinstance(field_id, str) or not field_id or field_id in fields.values():
            raise ValueError("Invalid field identifier")
        fields[name] = field_id

    tasks, page, total, pages = [], 1, None, None
    while pages is None or page <= pages:
        board = request(f"/task/tasks/{segment}?limit=100&page={page}")
        pagination, data = board["pagination"], board["data"]
        new_total, new_pages = pagination["total"], pagination["totalPages"]
        if (
            type(new_total) is not int
            or new_total < 0
            or type(new_pages) is not int
            or new_pages != (new_total + 99) // 100
            or (total is not None and (total, pages) != (new_total, new_pages))
        ):
            raise ValueError("Incomplete or changing task pagination")
        total, pages = new_total, new_pages
        buckets = [column["tasks"] for column in data["columns"]]
        buckets += [data["archivedTasks"], data["plannedTasks"]]
        for bucket in buckets:
            if not isinstance(bucket, list):
                raise ValueError("Invalid board bucket")
            for task in bucket:
                if (
                    not isinstance(task.get("id"), str)
                    or not task["id"]
                    or task.get("projectId") != project
                    or not isinstance(task.get("title"), str)
                    or not task["title"].strip()
                ):
                    raise ValueError("Invalid board task")
                tasks.append({"id": task["id"], "title": task["title"]})
        page += 1
    if len(tasks) != total or len({row["id"] for row in tasks}) != total:
        raise ValueError("Task listing was incomplete or duplicated")
    tasks.sort(key=lambda row: row["id"])
    task_ids = {row["id"] for row in tasks}
    values = request(f"/custom-field/project/{segment}/values")
    if not isinstance(values, list):
        raise ValueError("Invalid project field values")
    by_task, by_identity = {}, {}
    for row in values:
        if row.get("fieldId") != fields["POC TMDB ID"]:
            continue
        task, value = row.get("taskId"), row.get("value")
        if task not in task_ids or task in by_task:
            raise ValueError("Invalid or duplicate identity field row")
        by_task[task] = value
        if value in (None, ""):
            continue
        if (
            not isinstance(value, str)
            or not value.isascii()
            or not value.isdigit()
            or str(int(value)) != value
            or not 0 < int(value) <= 2147483647
            or value in by_identity
        ):
            raise ValueError("Invalid or duplicate film identity")
        by_identity[value] = task
    for task in tasks:
        task["tmdb_id"] = by_task.get(task["id"])
    return fields, tasks


def plan(request, project, sidecar, snapshot, status, approved_ids, source_hash, status_hash):
    if not isinstance(project, str) or not project.isalnum():
        raise ValueError("Invalid project identifier")
    user = request("/user/me")
    owner = user.get("id") if isinstance(user, dict) else None
    projection = project_watchlist(snapshot, status, [])
    view = {key: projection[key] for key in ("version", "source", "observed_at", "entries")}
    if (
        not isinstance(owner, str)
        or not owner
        or not isinstance(sidecar, dict)
        or set(sidecar) != {"version", "project_id", "users"}
        or sidecar.get("version") != "tracker-poc-movary-watchlist-users-v1"
        or sidecar.get("project_id") != project
        or not isinstance(sidecar.get("users"), dict)
        or sidecar["users"].get(owner) != view
        or len(view["entries"]) != 2
    ):
        raise ValueError("Key owner, project or watchlist observation differs")
    fields, tasks = inventory(request, project)
    pending, existing, conflicts = [], 0, 0
    for entry in view["entries"]:
        ident, title = entry["tmdb_id"], entry["title"]
        if not isinstance(title, str) or not title.strip():
            conflicts += 1
            continue
        id_matches = [row for row in tasks if row["tmdb_id"] == str(ident)]
        title_matches = [row for row in tasks if title_key(row["title"]) == title_key(title)]
        if id_matches:
            if len(title_matches) != 1 or title_matches[0]["id"] != id_matches[0]["id"]:
                conflicts += 1
            else:
                existing += 1
        elif ident in approved_ids or title_matches:
            conflicts += 1
        else:
            pending.append({"tmdb_id": ident, "title": title})
    if len({title_key(entry["title"]) for entry in pending}) != len(pending):
        conflicts += 1
    return {
        "version": VERSION,
        "project_id": project,
        "owner_id": owner,
        "snapshot_sha256": source_hash,
        "status_sha256": status_hash,
        "watchlist_sha256": digest(sidecar),
        "provider_approval_sha256": digest(sorted(approved_ids)),
        "fields": fields,
        "tasks_sha256": digest(tasks),
        "pending": pending,
        "existing": existing,
        "conflicts": conflicts,
    }


def neutral_body(entry, fields):
    values = (str(entry["tmdb_id"]), PUBLIC_IDENTITY_PROVENANCE, PUBLIC_FIELD_PROVENANCE)
    return {
        "title": entry["title"],
        "description": "",
        "priority": "no-priority",
        "status": "to-do",
        "customFields": [
            {"fieldId": fields[name], "value": value}
            for name, value in zip(FIELD_NAMES, values, strict=True)
        ],
    }


def apply(request, reviewed, load_current):
    if reviewed.get("version") != VERSION or reviewed.get("conflicts"):
        raise ValueError("Reviewed preview contains conflicts")
    if load_current() != reviewed:
        raise ValueError("Source, approval or project changed since preview")
    fixed = (
        "version",
        "project_id",
        "owner_id",
        "snapshot_sha256",
        "status_sha256",
        "watchlist_sha256",
        "provider_approval_sha256",
        "fields",
    )
    created = 0
    for entry in reviewed["pending"]:
        current = load_current()
        if (
            any(current[key] != reviewed[key] for key in fixed)
            or current["conflicts"]
            or current["pending"] != reviewed["pending"][created:]
            or current["existing"] != reviewed["existing"] + created
        ):
            raise ValueError("Film identity or title changed; inspect before retrying")
        try:
            result = request(
                "/task/" + quote(reviewed["project_id"], safe=""),
                neutral_body(entry, reviewed["fields"]),
            )
            task = result.get("id")
            if not isinstance(task, str) or not task:
                raise ValueError("Missing task ID")
            segment = quote(task, safe="")
            record = request("/task/" + segment)
            rows = request("/custom-field/task/" + segment)
            expected = neutral_body(entry, reviewed["fields"])["customFields"]
            if (
                record.get("id") != task
                or record.get("projectId") != reviewed["project_id"]
                or record.get("title") != entry["title"]
                or record.get("status") != "to-do"
                or any(
                    [row.get("value") for row in rows if row.get("fieldId") == field["fieldId"]]
                    != [field["value"]]
                    for field in expected
                )
            ):
                raise ValueError("Created task readback differs")
        except Exception:
            raise RuntimeError("Creation outcome unconfirmed; inspect before retrying") from None
        created += 1
    return {"status": "applied", "created": created}


def main():
    from tmdb_cache_batch import identities
    from youtrack_watched_property_backup import private_path
    from youtrack_watchlist_films import write_preview

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--preview", type=Path, required=True)
    parser.add_argument("--base", default="http://localhost:15173")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    base = urlsplit(args.base)
    if (
        base.scheme != "http"
        or base.hostname not in ("localhost", "127.0.0.1")
        or base.username
        or base.password
        or base.path not in ("", "/")
        or base.query
        or base.fragment
    ):
        raise ValueError("Only a local Kaneo origin is supported")
    snapshot = private_existing(args.snapshot)
    status = private_existing(snapshot.with_suffix(snapshot.suffix + ".status"))
    sidecar = private_existing(PRIVATE / "movary-watchlist.json")
    config = private_existing(PRIVATE / "kaneo-private-ids.json")
    opener = api_key_opener(os.environ.get("KANEO_API_KEY"))

    def request(path, payload=None):
        return call(opener, args.base.rstrip("/"), path, payload)

    def load_current():
        source_bytes, status_bytes = snapshot.read_bytes(), status.read_bytes()
        return plan(
            request,
            json.loads(config.read_text())["project"],
            json.loads(sidecar.read_text()),
            json.loads(source_bytes),
            json.loads(status_bytes),
            identities(),
            hashlib.sha256(source_bytes).hexdigest(),
            hashlib.sha256(status_bytes).hexdigest(),
        )

    if args.apply:
        reviewed = json.loads(private_path(args.preview, existing=True).read_text())
        print(json.dumps(apply(request, reviewed, load_current)))
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
    try:
        main()
    except Exception:
        print(
            "Import was not confirmed; inspect the private preview and target before retrying.",
            file=sys.stderr,
        )
        raise SystemExit(1) from None
