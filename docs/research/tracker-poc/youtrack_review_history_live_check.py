"""Verify text-field history on a newly created fictional FILMPOC issue.

This tests the history guard directly, not the importer. Each run creates and
retains one uniquely identified issue; it verifies its project and contents
before modifying the review field. It never uses browser credentials.
"""

import secrets
from urllib.parse import quote

from youtrack_client import YouTrackClient, YouTrackError
from youtrack_enrich import custom_value
from youtrack_review_import import (
    ISSUE_FIELDS,
    REVIEW_FIELD,
    empty_review_field,
    review_field_was_changed,
)
from youtrack_review_live_check import SmallActivityPages
from youtrack_setup import project_id


def main() -> None:
    client = YouTrackClient()
    project = project_id(client, "FILMPOC")
    issues = client.pages(
        "issues",
        query={"fields": ISSUE_FIELDS, "query": "project: {FILMPOC} sort by: {issue id} asc"},
    )
    used = {
        value for issue in issues if type(value := custom_value(issue, "FilmIQ TMDB ID")) is int
    }
    identity = next(
        (
            value
            for _ in range(10)
            if (value := 1_000_000_000 + secrets.randbelow(1_000_000_000)) not in used
        ),
        None,
    )
    if identity is None:
        raise YouTrackError("Could not allocate a unique fictional identity")
    marker = secrets.token_hex(8)
    title = "Fictional review history " + marker
    description = "Fictional synopsis " + marker
    source_evidence = "Fictional source evidence " + marker
    created = client.request(
        "issues",
        query={"fields": "id,idReadable"},
        body={
            "project": {"id": project},
            "summary": title,
            "description": description,
            "customFields": [
                {"name": "FilmIQ TMDB ID", "$type": "SimpleIssueCustomField", "value": identity},
                {
                    "name": "FilmIQ Source Evidence",
                    "$type": "TextIssueCustomField",
                    "value": {"text": source_evidence},
                },
            ],
        },
    )
    if not isinstance(created, dict):
        raise YouTrackError("Fictional fixture creation was not confirmed; inspect before retry")
    readable, record_id = created.get("idReadable"), created.get("id")
    if (
        not isinstance(readable, str)
        or not readable.startswith("FILMPOC-")
        or not isinstance(record_id, str)
    ):
        raise YouTrackError("Fictional fixture creation was not confirmed; inspect before retry")
    path = "issues/" + quote(record_id, safe="")
    current = client.request(
        path, query={"fields": ISSUE_FIELDS + ",description,project(id,shortName)"}
    )
    evidence = custom_value(current, "FilmIQ Source Evidence")
    current_project = current.get("project")
    if (
        current.get("id") != record_id
        or current.get("idReadable") != readable
        or not isinstance(current_project, dict)
        or current_project.get("id") != project
        or current_project.get("shortName") != "FILMPOC"
        or current.get("summary") != title
        or current.get("description") != description
        or custom_value(current, "FilmIQ TMDB ID") != identity
        or not isinstance(evidence, dict)
        or evidence.get("text") != source_evidence
        or not empty_review_field(current, required=True)
        or review_field_was_changed(client, record_id)
    ):
        raise YouTrackError("Fixture state is unexpected; no write allowed")
    value = "Fictional source link value"
    client.request(
        path,
        body={
            "customFields": [
                {"name": REVIEW_FIELD, "$type": "TextIssueCustomField", "value": {"text": value}}
            ]
        },
    )
    recorded = client.request(path, query={"fields": ISSUE_FIELDS})
    recorded_value = custom_value(recorded, REVIEW_FIELD)
    if not isinstance(recorded_value, dict) or recorded_value.get("text") != value:
        raise YouTrackError("Fictional write not confirmed; no clear attempted")
    client.request(
        path,
        body={
            "customFields": [{"name": REVIEW_FIELD, "$type": "TextIssueCustomField", "value": None}]
        },
    )
    cleared = client.request(path, query={"fields": ISSUE_FIELDS + ",description"})
    if not empty_review_field(cleared, required=True):
        raise YouTrackError("Fictional clear not confirmed")
    paged = SmallActivityPages(client, path + "/activities")
    if not review_field_was_changed(paged, record_id) or paged.nonempty_pages < 2:
        raise YouTrackError("Fictional field change was not found across multiple pages")
    if (
        cleared.get("description") != description
        or custom_value(cleared, "FilmIQ Source Evidence") != evidence
    ):
        raise YouTrackError("Unrelated fictional content changed")
    print(
        "FILMPOC: text field assignment and clear found across paginated history; fixture retained"
    )


if __name__ == "__main__":
    main()
