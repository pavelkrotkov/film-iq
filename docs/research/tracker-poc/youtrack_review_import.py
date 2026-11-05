"""Import reviewed direct-link assertions into an isolated YouTrack POC project.

The source manifest and reviewed links are validated before tracker writes.
Only a previously empty direct-links field is filled; existing issue content and
preferences are left untouched. Run a single importer at a time. A failed write
is not retried automatically: inspect the record and rerun after resolving it.
"""

import argparse
import json
from pathlib import Path
from typing import Any
from urllib.parse import quote

from direct_review_links import validate_review_manifests
from youtrack_client import YouTrackClient, YouTrackError
from youtrack_enrich import custom_value
from youtrack_setup import project_id

REVIEW_FIELD = "FilmIQ Direct Review Links"
ISSUE_FIELDS = "id,idReadable,summary,customFields(id,name,value(text))"


def ensure_review_field(client: YouTrackClient, project: str) -> None:
    """Create and attach only the dedicated optional text field, if needed."""
    path = "admin/customFieldSettings/customFields"
    fields = client.pages(path, query={"fields": "id,name,fieldType(id)"})
    matches = [item for item in fields if item.get("name") == REVIEW_FIELD]
    if len(matches) > 1:
        raise YouTrackError("Direct review field is ambiguous")
    if matches:
        field = matches[0]
        if field.get("fieldType", {}).get("id") != "text":
            raise YouTrackError("Direct review field has an unexpected type")
    else:
        field = client.request(
            path,
            query={"fields": "id,name,fieldType(id)"},
            body={
                "name": REVIEW_FIELD,
                "fieldType": {"id": "text"},
                "isAutoAttached": False,
                "isPublic": True,
            },
        )
    if not isinstance(field, dict) or not isinstance(field.get("id"), str):
        raise YouTrackError("Direct review field creation was not confirmed")
    path = f"admin/projects/{quote(project, safe='')}/customFields"
    attached = client.pages(path, query={"fields": "id,field(id,name)"})
    matches = [item for item in attached if item.get("field", {}).get("id") == field["id"]]
    if len(matches) > 1:
        raise YouTrackError("Direct review field is attached more than once")
    if not matches:
        client.request(
            path,
            body={
                "field": {"id": field["id"]},
                "$type": "TextProjectCustomField",
                "canBeEmpty": True,
            },
        )


def empty_review_field(issue: dict[str, Any], *, required: bool) -> bool:
    matches = [item for item in issue.get("customFields", []) if item.get("name") == REVIEW_FIELD]
    if len(matches) > 1 or (required and not matches):
        raise YouTrackError("Direct review field is missing or ambiguous")
    if not matches or matches[0].get("value") is None:
        return True
    value = matches[0]["value"]
    if not isinstance(value, dict) or "text" not in value:
        raise YouTrackError("Direct review field value is invalid")
    if value["text"] is None or value["text"] == "":
        return True
    if not isinstance(value["text"], str):
        raise YouTrackError("Direct review field value is invalid")
    return False


def combine_batches(
    manifests: list[dict[str, Any]], source: dict[str, Any]
) -> tuple[list[dict[str, Any]], int]:
    """Use the shared batch validator to hold back conflicts across all batches."""
    return validate_review_manifests(manifests, source)


def combine(manifests: list[dict[str, Any]], source: dict[str, Any]) -> list[dict[str, Any]]:
    return combine_batches(manifests, source)[0]


def run(
    client: YouTrackClient, manifests: list[dict[str, Any]], source: dict[str, Any], project: str
) -> tuple[int, int, int, int]:
    """Return written, preserved, title-conflict and manual-review counts."""
    if project not in {"FILMPOC", "FILMREAL"}:
        raise ValueError("Only the two local POC projects are supported")
    films, review_needed = combine_batches(manifests, source)
    if not films:
        return 0, 0, 0, review_needed
    titles = {film["tmdb_id"]: film["title"] for film in source["films"]}
    project_entity = project_id(client, project)
    records = client.pages(
        "issues",
        query={
            "fields": ISSUE_FIELDS,
            "query": f"project: {{{project}}} sort by: {{issue id}} asc",
        },
    )
    indexed: dict[int, dict[str, Any]] = {}
    for issue in records:
        identity = custom_value(issue, "FilmIQ TMDB ID")
        if identity is None:
            continue
        if type(identity) is not int or identity <= 0 or identity in indexed:
            raise YouTrackError("Project film IDs are invalid or duplicated")
        indexed[identity] = issue
    targets = []
    conflicts = 0
    for film in films:
        issue = indexed.get(film["tmdb_id"])
        if issue is None:
            raise YouTrackError("A reviewed film has no unique project record")
        record_id, readable = issue.get("id"), issue.get("idReadable")
        if (
            not isinstance(record_id, str)
            or not isinstance(readable, str)
            or not readable.startswith(project + "-")
        ):
            raise YouTrackError("A reviewed film has an invalid project record")
        empty_review_field(issue, required=False)
        if issue.get("summary") != titles[film["tmdb_id"]]:
            conflicts += 1
            continue
        targets.append((film, record_id))
    if not targets:
        return 0, 0, conflicts, review_needed
    ensure_review_field(client, project_entity)
    written = preserved = 0
    for film, record_id in targets:
        path = "issues/" + quote(record_id, safe="")
        current = client.request(path, query={"fields": ISSUE_FIELDS})
        if (
            current.get("id") != record_id
            or current.get("idReadable") != indexed[film["tmdb_id"]]["idReadable"]
            or custom_value(current, "FilmIQ TMDB ID") != film["tmdb_id"]
        ):
            raise YouTrackError("Film identity changed; inspect before retrying")
        if current.get("summary") != titles[film["tmdb_id"]]:
            conflicts += 1
            continue
        if not empty_review_field(current, required=True):
            preserved += 1
            continue
        payload = {"schema_version": 1, "tmdb_id": film["tmdb_id"], "links": film["links"]}
        client.request(
            path,
            body={
                "customFields": [
                    {
                        "name": REVIEW_FIELD,
                        "$type": "TextIssueCustomField",
                        "value": {"text": json.dumps(payload, ensure_ascii=False, sort_keys=True)},
                    }
                ]
            },
        )
        written += 1
    return written, preserved, conflicts, review_needed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, action="append", type=Path)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--project", required=True, choices=("FILMPOC", "FILMREAL"))
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    manifests = [json.loads(path.read_text(encoding="utf-8")) for path in args.manifest]
    source = json.loads(args.source.read_text(encoding="utf-8"))
    films, review_needed = combine_batches(manifests, source)
    if not args.apply:
        print(
            f"Validated {len(films)} film link groups; "
            f"manual-review groups: {review_needed}; no changes made"
        )
        return
    written, preserved, conflicts, review_needed = run(
        YouTrackClient(), manifests, source, args.project
    )
    print(
        f"Direct review links: {written} fields filled, {preserved} existing fields preserved, "
        f"{conflicts} edited-title conflicts skipped, manual-review groups: {review_needed}"
    )


if __name__ == "__main__":
    main()
