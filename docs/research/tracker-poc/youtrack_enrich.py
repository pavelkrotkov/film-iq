"""Synthetic enrichment adapter backed by native YouTrack issues and fields."""

import json
from typing import Any
from urllib.parse import quote

from enrichment import FilmMetadata
from youtrack_client import YouTrackClient, YouTrackError
from youtrack_setup import project_id

ISSUE_FIELDS = "id,idReadable,summary,description,customFields(id,name,value)"
YEAR_FIELD = "FilmIQ Release Year"
GENRE_FIELD = "FilmIQ Genre"


def custom_value(issue: dict[str, Any], name: str) -> Any:
    matching = [field for field in issue.get("customFields", []) if field.get("name") == name]
    if len(matching) != 1:
        raise YouTrackError(f"Expected one {name!r} custom field")
    return matching[0].get("value")


class YouTrackFixtureBackend:
    """Use fixture IDs; only backfill fields with no prior change in their history.

    Run one worker without concurrent edits: YouTrack does not offer a
    compare-and-swap for these updates.
    """

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
        if film.year is not None and (type(film.year) is not int or not 0 < film.year <= 9999):
            raise ValueError("Fixture release year must be a positive integer")
        if film.genre is not None and not isinstance(film.genre, str):
            raise ValueError("Fixture genre must be text")
        metadata = {
            YEAR_FIELD: film.year,
            GENRE_FIELD: film.genre if film.genre and film.genre.strip() else None,
        }
        matches = [
            issue
            for issue in self.issues()
            if custom_value(issue, "FilmIQ Fixture ID") == film.source_id
        ]
        if len(matches) > 1:
            raise YouTrackError("Fixture ID is duplicated; manual resolution required")
        if matches:
            issue = matches[0]
            record_id = issue.get("id")
            if not isinstance(record_id, str):
                raise YouTrackError("Fixture record has no ID")
            missing = {}
            for name, value in metadata.items():
                if value is None:
                    continue
                fields = [
                    item for item in issue.get("customFields", []) if item.get("name") == name
                ]
                if len(fields) != 1 or "value" not in fields[0]:
                    raise YouTrackError("Fixture field value is unavailable; no backfill allowed")
                if fields[0]["value"] is None:
                    missing[name] = value
            if missing:
                history = self.client.pages(
                    f"issues/{quote(record_id, safe='')}/activities",
                    query={"categories": "CustomFieldCategory", "fields": "id,field(name)"},
                )
                for event in history:
                    field = event.get("field")
                    if not isinstance(field, dict) or not isinstance(field.get("name"), str):
                        raise YouTrackError("Custom-field history cannot be interpreted")
                    missing.pop(field["name"], None)
                if missing:
                    self.client.request(
                        f"issues/{quote(record_id, safe='')}",
                        body={
                            "customFields": [
                                {"name": name, "$type": "SimpleIssueCustomField", "value": value}
                                for name, value in missing.items()
                            ]
                        },
                    )
            return record_id
        fields: list[dict[str, Any]] = [
            {
                "name": "FilmIQ Fixture ID",
                "$type": "SimpleIssueCustomField",
                "value": film.source_id,
            }
        ]
        for name, value in metadata.items():
            if value is None:
                continue
            fields.append(
                {
                    "name": name,
                    "$type": "SimpleIssueCustomField",
                    "value": value,
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
