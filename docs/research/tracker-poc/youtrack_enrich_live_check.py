"""Check the fixture worker against local YouTrack, creating two FILMPOC issues.

Each run leaves two new fictional issues in FILMPOC. Run only against the
dedicated local POC instance, without concurrent edits. No preferences, real
film projects, external services, or live TMDB metadata are accessed.
"""

import json
import secrets
import sys
from datetime import UTC, datetime
from typing import Any
from urllib.parse import quote

from enrichment import FilmMetadata, FixtureSource, enrich
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


class Availability(FixtureSource):
    def __init__(self, *, changed: bool = False, partial: bool = False, failed: bool = False):
        self.changed, self.partial, self.failed = changed, partial, failed

    def availability(self, source_id: int) -> dict | None:
        if self.failed:
            raise RuntimeError("Synthetic source failure")
        return {
            "id": source_id,
            "results": {
                "US": {
                    "link": "https://example.invalid/fictional",
                    "flatrate": [{}]
                    if self.partial
                    else [
                        {
                            "provider_id": 101,
                            "provider_name": "Fixture Stream 2"
                            if self.changed
                            else "Fixture Stream",
                        }
                    ],
                    "rent": [{"provider_id": 102, "provider_name": "Fixture Rental"}],
                    "buy": [{"provider_id": 103, "provider_name": "Fixture Purchase"}],
                }
            },
        }


def observation(client: YouTrackClient, path: str) -> dict:
    issue = client.request(path, query={"fields": "id,customFields(id,name,value)"})
    field = next(f for f in issue["customFields"] if f["name"] == "FilmIQ Provider Observation")
    detail = client.request(
        path + "/customFields/" + quote(field["id"], safe=""),
        query={"fields": "id,value(text)"},
    )
    return json.loads(detail["value"]["text"])


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

        stage = "fictional-availability-refresh"
        now = datetime.now(UTC)
        require(enrich(Availability(), backend, identities[1], now) == second, "Issue changed")
        initial = observation(client, issue_path)
        require(
            initial["subscription"] == ["Fixture Stream"]
            and initial["rent"] == ["Fixture Rental"]
            and initial["buy"] == ["Fixture Purchase"],
            "Fictional offer categories were not stored separately",
        )
        require(
            enrich(Availability(changed=True), backend, identities[1], now) == second,
            "Issue changed",
        )
        refreshed = observation(client, issue_path)
        require(
            refreshed["subscription"] == ["Fixture Stream 2"]
            and refreshed["rent"] == ["Fixture Rental"]
            and refreshed["buy"] == ["Fixture Purchase"],
            "Fictional availability refresh did not persist",
        )
        require(
            enrich(Availability(partial=True), backend, identities[1], now) == second,
            "Issue changed",
        )
        try:
            enrich(Availability(failed=True), backend, identities[1], now)
        except RuntimeError:
            pass
        else:
            raise ValueError("Synthetic provider failure was not reported")
        require(observation(client, issue_path) == refreshed, "Failed refresh changed availability")
        after = client.request(
            issue_path, query={"fields": "id,description,customFields(name,value(name))"}
        )
        require(
            after["description"] == "User-edited fictional synopsis."
            and (custom_value(after, "FilmIQ Lifecycle") or {}).get("name") == "Evaluation"
            and sum(
                custom_value(issue, "FilmIQ Fixture ID") == identities[1]
                for issue in backend.issues()
            )
            == 1,
            "Fictional refresh changed user edits, lifecycle, or created a duplicate",
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
                "separateSubscriptionRentalPurchase": True,
                "refreshedAndFailurePreserved": True,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
