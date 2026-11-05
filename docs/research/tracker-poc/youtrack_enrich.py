"""Synthetic enrichment adapter backed by native YouTrack issues and fields."""

import json
from typing import Any
from urllib.parse import quote

from enrichment import FilmMetadata
from youtrack_client import YouTrackClient, YouTrackError
from youtrack_setup import project_id

ISSUE_FIELDS = "id,idReadable,summary,description,customFields(id,name,value)"


def custom_value(issue: dict[str, Any], name: str) -> Any:
    matching = [field for field in issue.get("customFields", []) if field.get("name") == name]
    if len(matching) != 1:
        raise YouTrackError(f"Expected one {name!r} custom field")
    return matching[0].get("value")


class YouTrackFixtureBackend:
    """Uses a separate fixture-ID field, never treating invented IDs as TMDB IDs."""

    def __init__(self, client: YouTrackClient) -> None:
        self.client = client
        self.project = project_id(client)

    def issues(self) -> list[dict[str, Any]]:
        return self.client.pages(
            "issues",
            query={
                "fields": ISSUE_FIELDS,
                "query": "project: {FILMPOC} sort by: {issue id} asc",
            },
        )

    def ensure_film(self, film: FilmMetadata) -> str:
        matches = [
            issue
            for issue in self.issues()
            if custom_value(issue, "FilmIQ Fixture ID") == film.source_id
        ]
        if len(matches) > 1:
            raise YouTrackError("Fixture ID is duplicated; manual resolution required")
        if matches:
            return str(matches[0]["id"])
        fields: list[dict[str, Any]] = [
            {
                "name": "FilmIQ Fixture ID",
                "$type": "SimpleIssueCustomField",
                "value": film.source_id,
            }
        ]
        if film.year is not None:
            fields.append(
                {
                    "name": "FilmIQ Release Year",
                    "$type": "SimpleIssueCustomField",
                    "value": film.year,
                }
            )
        created = self.client.request(
            "issues",
            query={"fields": "id,idReadable"},
            body={
                "summary": film.title,
                "description": film.synopsis,
                "project": {"id": self.project},
                "customFields": fields,
            },
        )
        if not isinstance(created, dict) or not isinstance(created.get("id"), str):
            raise YouTrackError("Issue creation returned no ID; check before retrying")
        return str(created["id"])

    def set_availability(self, record_id: str, value: dict[str, Any]) -> None:
        self.client.request(
            f"issues/{quote(record_id, safe='')}",
            body={
                "customFields": [
                    {
                        "name": "FilmIQ Provider Observation",
                        "$type": "TextIssueCustomField",
                        "value": {"text": json.dumps(value, sort_keys=True)},
                    }
                ]
            },
        )
