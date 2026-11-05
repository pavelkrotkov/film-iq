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
from youtrack_review_import import ISSUE_FIELDS, REVIEW_FIELD, combine, run
from youtrack_setup import project_id


def main() -> None:
    client = YouTrackClient()
    project = project_id(client, "FILMPOC")
    issues = client.pages(
        "issues",
        query={"fields": ISSUE_FIELDS, "query": "project: {FILMPOC} sort by: {issue id} asc"},
    )
    used = {custom_value(issue, "FilmIQ TMDB ID") for issue in issues}
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
    print(
        "FILMPOC: fictional import and unchanged retry passed; edited synopsis and evidence preserved"
    )


if __name__ == "__main__":
    main()
