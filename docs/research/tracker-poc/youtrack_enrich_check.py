"""Exercise synthetic enrichment, failure handling, and the YouTrack lifecycle."""

from datetime import UTC, datetime
from urllib.parse import quote

from enrichment import FixtureSource, enrich
from youtrack_client import YouTrackClient
from youtrack_enrich import YouTrackFixtureBackend


class MissingAvailability(FixtureSource):
    def availability(self, source_id: int) -> None:
        return None


def main() -> None:
    client = YouTrackClient()
    backend = YouTrackFixtureBackend(client)
    now = datetime.now(UTC)
    identity = 987654321  # Deliberately fictional; stored in a separate fixture field.
    record = enrich(FixtureSource(), backend, identity, now)
    assert enrich(FixtureSource(), backend, identity, now) == record
    path = "issues/" + quote(record, safe="")
    user_synopsis = "Fictional synopsis edited by a synthetic user."
    client.request(path, body={"description": user_synopsis})
    states = ["Discovery", "Evaluation", "Watchlist", "Archived", "Discovery"]
    for state in states:
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
        result = client.request(
            path, query={"fields": "id,description,customFields(id,name,value)"}
        )
        state_field = next(
            item for item in result["customFields"] if item["name"] == "FilmIQ Lifecycle"
        )
        state_path = path + "/customFields/" + quote(state_field["id"], safe="")
        actual = client.request(state_path, query={"fields": "id,value(name)"})["value"]
        assert actual["name"] == state and result["description"] == user_synopsis
    issue = client.request(path, query={"fields": "id,description,customFields(id,name,value)"})
    observation = next(
        item for item in issue["customFields"] if item["name"] == "FilmIQ Provider Observation"
    )
    observation_path = path + "/customFields/" + quote(observation["id"], safe="")
    prior = client.request(observation_path, query={"fields": "id,value(text)"})["value"]["text"]
    assert enrich(MissingAvailability(), backend, identity, now) == record
    after = client.request(observation_path, query={"fields": "id,value(text)"})["value"]["text"]
    assert after == prior
    issue = client.request(path, query={"fields": "id,description"})
    assert issue["description"] == user_synopsis
    print("Synthetic YouTrack repeat import, lifecycle, and failure checks passed")


if __name__ == "__main__":
    main()
