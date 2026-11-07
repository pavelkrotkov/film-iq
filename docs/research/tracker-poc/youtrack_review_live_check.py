"""Run a fictional review-link round trip in FILMPOC; retains its test issue.

Run with: uv run python docs/research/tracker-poc/youtrack_review_live_check.py
Requires the local POC YouTrack administrator token and configured FILMPOC.
No external review sites, real source manifests or private projects are used.
"""

import json
import secrets
from urllib.parse import quote

from youtrack_client import YouTrackClient, YouTrackError
from youtrack_enrich import custom_value
from youtrack_review_import import (
    ISSUE_FIELDS,
    REVIEW_FIELD,
    combine,
    empty_review_field,
    review_field_was_changed,
    run,
)
from youtrack_setup import project_id


class SmallActivityPages(YouTrackClient):
    """Exercise real pagination with one fictional activity per page."""

    def __init__(self, client: YouTrackClient, activity_path: str) -> None:
        self.client = client
        self.activity_path = activity_path
        self.nonempty_pages = 0
        self.skips: list[int] = []

    def request(self, path, *, query=None, body=None):
        if path == self.activity_path and query and "$top" in query:
            query = {**query, "$top": 1}
            self.skips.append(int(query["$skip"]))
            result = self.client.request(path, query=query, body=body)
            if result:
                self.nonempty_pages += 1
            return result
        return self.client.request(path, query=query, body=body)


def used_identities(issues: list[dict]) -> set[int]:
    """Fail before creating a test issue if the project cannot be imported."""
    used: set[int] = set()
    for issue in issues:
        identity = custom_value(issue, "FilmIQ TMDB ID")
        if identity is None:
            continue
        if type(identity) is not int or identity <= 0 or identity in used:
            raise YouTrackError(
                "Synthetic project has invalid or duplicate IDs; no fixture created"
            )
        used.add(identity)
    return used


def main() -> None:
    client = YouTrackClient()
    project = project_id(client, "FILMPOC")
    issues = client.pages(
        "issues",
        query={"fields": ISSUE_FIELDS, "query": "project: {FILMPOC} sort by: {issue id} asc"},
    )
    used = used_identities(issues)
    identity = next(
        (
            value
            for _ in range(10)
            if (value := 1_000_000_000 + secrets.randbelow(1_000_000_000)) not in used
        ),
        None,
    )
    if identity is None:
        raise YouTrackError("Could not allocate a synthetic fixture identity")
    title = "Fictional review link test"
    created = client.request(
        "issues",
        query={"fields": "id"},
        body={
            "project": {"id": project},
            "summary": title,
            "description": "Initial fictional synopsis",
            "customFields": [
                {"name": "FilmIQ TMDB ID", "$type": "SimpleIssueCustomField", "value": identity},
                {
                    "name": "FilmIQ Source Evidence",
                    "$type": "TextIssueCustomField",
                    "value": {"text": "Fictional preexisting evidence"},
                },
            ],
        },
    )
    if not isinstance(created, dict) or not isinstance(created.get("id"), str):
        raise YouTrackError("Fixture creation was not confirmed; inspect before retrying")
    path = "issues/" + quote(created["id"], safe="")
    client.request(path, body={"description": "Edited fictional synopsis"})
    source = {
        "version": "tracker-poc-private-film-input-v1",
        "films": [
            {
                "tmdb_id": identity,
                "title": title,
                "director": "Fictional Director",
                "source_year": 2001,
                "origin": ["discovery"],
                "field_provenance": {"tmdb_id": "reviewed accepted identity match"},
            }
        ],
    }
    manifest = {
        "schema_version": 1,
        "films": [
            {
                "tmdb_id": identity,
                "links": [
                    {
                        "url": "https://example.com/synthetic-review",
                        "provider": "Fictional Critic",
                        "type": "individual_critic_review",
                        "checked_at": "2026-11-05T12:00:00+00:00",
                        "identity_evidence": {
                            "input_title": title,
                            "source_page_title": title,
                            "director": "Fictional Director",
                            "input_source_year": 2001,
                            "basis": "Fictional test assertion; no review page requested",
                        },
                    }
                ],
            }
        ],
    }
    assert run(client, [manifest], source, "FILMPOC") == (1, 0, 0, 0)
    assert run(client, [manifest], source, "FILMPOC") == (0, 1, 0, 0)
    issue = client.request(path, query={"fields": ISSUE_FIELDS + ",description"})
    assert issue["description"] == "Edited fictional synopsis"
    assert custom_value(issue, "FilmIQ Source Evidence")["text"] == "Fictional preexisting evidence"
    saved = json.loads(custom_value(issue, REVIEW_FIELD)["text"])
    assert saved == {
        "schema_version": 1,
        "tmdb_id": identity,
        "links": combine([manifest], source)[0]["links"],
    }
    if not str(issue.get("idReadable", "")).startswith("FILMPOC-"):
        raise YouTrackError("Fixture was not in the synthetic project; no clear allowed")
    client.request(
        path,
        body={
            "customFields": [{"name": REVIEW_FIELD, "$type": "TextIssueCustomField", "value": None}]
        },
    )
    cleared = client.request(path, query={"fields": ISSUE_FIELDS + ",description"})
    if not empty_review_field(cleared, required=True):
        raise YouTrackError("Fictional clear was not confirmed; no retry allowed")
    paged = SmallActivityPages(client, path + "/activities")
    assert review_field_was_changed(paged, created["id"])
    if paged.nonempty_pages < 2 or len(paged.skips) < 3:
        raise YouTrackError("Fictional history did not span multiple pages")
    assert run(paged, [manifest], source, "FILMPOC") == (0, 1, 0, 0)
    after = client.request(path, query={"fields": ISSUE_FIELDS + ",description"})
    assert empty_review_field(after, required=True)
    assert after["description"] == "Edited fictional synopsis"
    assert custom_value(after, "FilmIQ Source Evidence")["text"] == "Fictional preexisting evidence"
    print(
        "FILMPOC: fictional initial import, clear, paginated history, preservation and readback passed; "
        "fixture retained"
    )


if __name__ == "__main__":
    main()
