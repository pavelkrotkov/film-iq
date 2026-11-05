"""Check the fixture worker against local YouTrack, creating two FILMPOC issues.

Each run leaves two new fictional issues in FILMPOC. Run only against the
dedicated local POC instance, without concurrent edits. No preferences, real
film projects, external services, or live TMDB metadata are accessed.
"""

import json
import secrets
import sys
from typing import Any
from urllib.parse import quote

from enrichment import FilmMetadata
from youtrack_client import YouTrackClient
from youtrack_enrich import YouTrackFixtureBackend, custom_value


def film(identity: int, year: int | None, genre: str | None) -> FilmMetadata:
    return FilmMetadata(
        identity, "Fictional worker verification", "Fictional source synopsis.", year, genre
    )


def simple(name: str, value: Any) -> dict[str, Any]:
    return {"name": name, "$type": "SimpleIssueCustomField", "value": value}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def main() -> int:
    stage = "setup"
    try:
        client = YouTrackClient()
        backend = YouTrackFixtureBackend(client)
        used = {custom_value(issue, "FilmIQ Fixture ID") for issue in backend.issues()}
        identities: list[int] = []
        while len(identities) < 2:
            candidate = 1_000_000_000 + secrets.randbelow(1_000_000_000)
            if candidate not in used and candidate not in identities:
                identities.append(candidate)

        stage = "create-populated"
        first = backend.ensure_film(film(identities[0], 2001, "Fictional Drama"))
        row = client.request(
            "issues/" + quote(first, safe=""),
            query={"fields": "id,description,customFields(name,value)"},
        )
        require(
            custom_value(row, "FilmIQ Release Year") == 2001
            and custom_value(row, "FilmIQ Genre") == "Fictional Drama",
            "Fixture metadata was not stored on creation",
        )

        stage = "create-empty"
        second = backend.ensure_film(film(identities[1], None, None))
        require(first != second, "Fixture issues must be distinct")
        issue_path = "issues/" + quote(second, safe="")
        empty = client.request(
            issue_path, query={"fields": "id,description,customFields(name,value)"}
        )
        for name in ("FilmIQ Release Year", "FilmIQ Genre"):
            fields = [field for field in empty["customFields"] if field.get("name") == name]
            require(
                len(fields) == 1 and "value" in fields[0] and fields[0]["value"] is None,
                "An empty fixture field did not have an explicit null value",
            )

        stage = "backfill"
        require(
            backend.ensure_film(film(identities[1], 2002, "Fictional Comedy")) == second,
            "Backfill did not reuse the fixture issue",
        )
        filled = client.request(
            issue_path, query={"fields": "id,description,customFields(name,value)"}
        )
        require(
            custom_value(filled, "FilmIQ Release Year") == 2002
            and custom_value(filled, "FilmIQ Genre") == "Fictional Comedy",
            "Untouched fixture fields were not backfilled",
        )

        stage = "clear-and-preserve"
        client.request(
            issue_path,
            body={
                "description": "User-edited fictional synopsis.",
                "customFields": [
                    simple("FilmIQ Genre", None),
                    {
                        "name": "FilmIQ Lifecycle",
                        "$type": "StateIssueCustomField",
                        "value": {"name": "Evaluation"},
                    },
                ],
            },
        )
        history = client.pages(
            issue_path + "/activities",
            query={"categories": "CustomFieldCategory", "fields": "id,field(name)"},
        )
        require(
            all(
                isinstance(event.get("field"), dict) and isinstance(event["field"].get("name"), str)
                for event in history
            )
            and any(event["field"]["name"] == "FilmIQ Genre" for event in history),
            "Fixture genre history was unavailable",
        )
        require(
            backend.ensure_film(film(identities[1], 2003, "Fictional Animation")) == second,
            "Repeat enrichment did not reuse the fixture issue",
        )
        final = client.request(
            issue_path, query={"fields": "id,description,customFields(name,value(name))"}
        )
        require(
            custom_value(final, "FilmIQ Genre") is None
            and custom_value(final, "FilmIQ Release Year") == 2002
            and final.get("description") == "User-edited fictional synopsis."
            and (custom_value(final, "FilmIQ Lifecycle") or {}).get("name") == "Evaluation",
            "An existing fictional value or explicit clear was not preserved",
        )
    except Exception as error:
        print(
            json.dumps({"passed": False, "stage": stage, "errorType": type(error).__name__}),
            file=sys.stderr,
        )
        return 1
    print(
        json.dumps(
            {
                "passed": True,
                "fictionalIssuesCreated": 2,
                "explicitNulls": True,
                "historyPreservedClear": True,
                "synopsisLifecycleAndYearPreserved": True,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
