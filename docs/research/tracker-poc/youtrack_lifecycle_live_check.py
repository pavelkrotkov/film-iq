"""Exercise lifecycle transitions on one new fictional FILMPOC issue.

The issue is retained for inspection. This uses the local YouTrack integration
token and fixture provider only; no real film, Movary, or provider is changed.
Run with one fixture writer and do not retry an unconfirmed mutation blindly.
"""

import json
import secrets
import sys
from datetime import UTC, datetime
from urllib.parse import quote

from enrichment import enrich
from youtrack_client import YouTrackClient, YouTrackError
from youtrack_enrich import YouTrackFixtureBackend, custom_value
from youtrack_enrich_live_check import Availability, film, observation, require

STATES = ("Discovery", "Evaluation", "Watchlist", "Archived", "Evaluation")


def without_lifecycle(issue: dict) -> dict:
    fields = issue.get("customFields")
    if not isinstance(fields, list) or not all(
        isinstance(field, dict) and isinstance(field.get("name"), str) for field in fields
    ):
        raise ValueError("Issue field projection is unavailable")
    names = [field["name"] for field in fields]
    if len(names) != len(set(names)) or names.count("FilmIQ Lifecycle") != 1:
        raise ValueError("Issue fields are duplicated or lifecycle is unavailable")
    return {
        **issue,
        "customFields": sorted(
            (field for field in fields if field["name"] != "FilmIQ Lifecycle"),
            key=lambda field: field["name"],
        ),
    }


def main() -> int:
    stage = "setup"
    try:
        client = YouTrackClient()
        backend = YouTrackFixtureBackend(client)
        used = {custom_value(issue, "FilmIQ Fixture ID") for issue in backend.issues()}
        identity = 1_000_000_000 + secrets.randbelow(1_000_000_000)
        if identity in used:
            raise ValueError("Fictional ID already exists; stop before creating")

        stage = "create"
        record_id = backend.ensure_film(film(identity, 2001, "Fictional Drama"))
        path = "issues/" + quote(record_id, safe="")
        query: dict[str, str | int] = {
            "fields": "id,idReadable,project(shortName),summary,description,customFields(name,value(name,text))"
        }
        issue = client.request(path, query=query)
        require(
            issue.get("id") == record_id
            and issue.get("project", {}).get("shortName") == "FILMPOC"
            and str(issue.get("idReadable", "")).startswith("FILMPOC-")
            and custom_value(issue, "FilmIQ Fixture ID") == identity,
            "Created issue is not the intended fictional fixture",
        )

        stage = "enrich"
        require(
            enrich(Availability(), backend, identity, datetime.now(UTC)) == record_id,
            "Record changed",
        )
        expected_offers = observation(client, path)
        require(
            expected_offers["subscription"] == ["Fixture Stream"]
            and expected_offers["rent"] == ["Fixture Rental"]
            and expected_offers["buy"] == ["Fixture Purchase"],
            "Fixture availability was not stored",
        )
        baseline = without_lifecycle(client.request(path, query=query))

        def check(expected: str) -> None:
            row = client.request(path, query=query)
            state = custom_value(row, "FilmIQ Lifecycle")
            require(
                row.get("id") == record_id
                and row.get("project", {}).get("shortName") == "FILMPOC"
                and row.get("summary") == "Fictional worker verification"
                and row.get("description") == "Fictional source synopsis."
                and custom_value(row, "FilmIQ Fixture ID") == identity
                and custom_value(row, "FilmIQ Release Year") == 2001
                and custom_value(row, "FilmIQ Genre") == "Fictional Drama"
                and isinstance(state, dict)
                and state.get("name") == expected
                and without_lifecycle(row) == baseline
                and observation(client, path) == expected_offers,
                "Fixture lifecycle readback or metadata preservation failed",
            )

        for state in STATES:
            stage = "transition-" + state.lower()
            client.request(
                path,
                body={
                    "customFields": [
                        {
                            "name": "FilmIQ Lifecycle",
                            "$type": "StateIssueCustomField",
                            "value": {"name": state},
                        }
                    ]
                },
            )
            check(state)
    except (YouTrackError, ValueError, KeyError, TypeError, OSError) as error:
        print(
            json.dumps({"passed": False, "stage": stage, "errorType": type(error).__name__}),
            file=sys.stderr,
        )
        return 1
    print(
        json.dumps(
            {
                "passed": True,
                "fictionalIssuesCreated": 1,
                "lifecycleTransitions": len(STATES),
                "metadataAndAvailabilityPreserved": True,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
