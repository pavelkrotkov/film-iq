"""Deterministic fixture-only checks for YouTrack enrichment preservation."""

from copy import deepcopy
from typing import Any, cast

from enrichment import FilmMetadata
from youtrack_client import YouTrackClient, YouTrackError
from youtrack_enrich import YouTrackFixtureBackend, custom_value


class FakeClient:
    def __init__(self):
        self.records: dict[str, dict[str, Any]] = {}
        self.history: dict[str, list[dict[str, Any]]] = {}
        self.updates = 0
        self.preferences = {"fictional-user": {"interest_score": 8, "watched_at": None}}

    def pages(self, path, *, query):
        if path == "admin/projects":
            return [{"id": "project-1", "shortName": "FILMPOC"}]
        if path == "issues":
            return deepcopy(list(self.records.values()))
        if path.startswith("issues/") and path.endswith("/activities"):
            return deepcopy(self.history[path.split("/")[1]])
        raise AssertionError(f"Unexpected read: {path}")

    def request(self, path, *, query=None, body=None):
        if path == "issues":
            assert body is not None
            record_id = f"issue-{len(self.records) + 1}"
            record: dict[str, Any] = {
                "id": record_id,
                "summary": body["summary"],
                "description": body["description"],
                "customFields": [
                    {"name": name, "value": None}
                    for name in (
                        "FilmIQ Fixture ID",
                        "FilmIQ Release Year",
                        "FilmIQ Genre",
                        "FilmIQ Lifecycle",
                    )
                ],
            }
            self.records[record_id] = record
            self.history[record_id] = []
        else:
            record_id = path.split("/")[1]
            record = self.records[record_id]
            if body is None:
                return deepcopy(record)
            self.updates += 1
        assert body is not None
        if "description" in body:
            record["description"] = body["description"]
        for incoming in body.get("customFields", []):
            target = next(
                field for field in record["customFields"] if field["name"] == incoming["name"]
            )
            target["value"] = deepcopy(incoming["value"])
            self.history[record_id].append({"id": "event", "field": {"name": incoming["name"]}})
        return {"id": record_id}


def film(identity, year, genre):
    return FilmMetadata(identity, f"Fictional {identity}", "Source synopsis", year, genre)


def check():
    client = FakeClient()
    backend = YouTrackFixtureBackend(cast(YouTrackClient, client))
    created = backend.ensure_film(film(1, 2001, "Drama"))
    assert custom_value(client.records[created], "FilmIQ Release Year") == 2001
    assert custom_value(client.records[created], "FilmIQ Genre") == "Drama"
    assert backend.ensure_film(film(1, 2010, "Comedy")) == created
    assert client.updates == 0

    pending = backend.ensure_film(film(2, None, None))
    client.request(f"issues/{pending}", body={"description": "User synopsis"})
    preferences = deepcopy(client.preferences)
    assert backend.ensure_film(film(2, 2002, "Comedy")) == pending
    assert custom_value(client.records[pending], "FilmIQ Release Year") == 2002
    assert custom_value(client.records[pending], "FilmIQ Genre") == "Comedy"
    assert client.records[pending]["description"] == "User synopsis"
    assert client.preferences == preferences
    before = client.updates
    assert backend.ensure_film(film(2, 2003, "Drama")) == pending
    assert client.updates == before

    for state in ("Discovery", "Evaluation", "Watchlist", "Archived", "Discovery"):
        client.request(
            f"issues/{pending}",
            body={"customFields": [{"name": "FilmIQ Lifecycle", "value": {"name": state}}]},
        )
        backend.ensure_film(film(2, 2003, "Drama"))
        reloaded = client.request(f"issues/{pending}")
        assert custom_value(reloaded, "FilmIQ Lifecycle")["name"] == state
        assert custom_value(reloaded, "FilmIQ Release Year") == 2002
        assert custom_value(reloaded, "FilmIQ Genre") == "Comedy"
        assert reloaded["description"] == "User synopsis" and client.preferences == preferences

    client.request(
        f"issues/{pending}",
        body={
            "customFields": [
                {"name": "FilmIQ Release Year", "value": None},
                {"name": "FilmIQ Genre", "value": None},
            ]
        },
    )
    before = client.updates
    backend.ensure_film(film(2, 2003, "Drama"))
    assert client.updates == before
    assert custom_value(client.records[pending], "FilmIQ Release Year") is None
    assert custom_value(client.records[pending], "FilmIQ Genre") is None

    partial = backend.ensure_film(film(5, None, None))
    client.request(
        f"issues/{partial}",
        body={
            "customFields": [
                {"name": "FilmIQ Release Year", "value": 1999},
                {"name": "FilmIQ Release Year", "value": None},
            ]
        },
    )
    backend.ensure_film(film(5, 2005, "Animation"))
    assert custom_value(client.records[partial], "FilmIQ Release Year") is None
    assert custom_value(client.records[partial], "FilmIQ Genre") == "Animation"

    blank = backend.ensure_film(film(6, None, None))
    client.request(
        f"issues/{blank}", body={"customFields": [{"name": "FilmIQ Genre", "value": ""}]}
    )
    backend.ensure_film(film(6, 2006, "Drama"))
    assert custom_value(client.records[blank], "FilmIQ Genre") == ""
    assert custom_value(client.records[blank], "FilmIQ Release Year") == 2006

    bad = backend.ensure_film(film(3, None, None))
    client.history[bad].append({"id": "bad", "field": None})
    try:
        backend.ensure_film(film(3, 2001, "Drama"))
    except YouTrackError:
        pass
    else:
        raise AssertionError("Uninterpretable history allowed a backfill")
    assert custom_value(client.records[bad], "FilmIQ Genre") is None

    missing_value = backend.ensure_film(film(4, None, None))
    next(
        field
        for field in client.records[missing_value]["customFields"]
        if field["name"] == "FilmIQ Genre"
    ).pop("value")
    try:
        backend.ensure_film(film(4, 2001, "Drama"))
    except YouTrackError:
        pass
    else:
        raise AssertionError("An omitted field value allowed a backfill")
    print(
        "Synthetic YouTrack create, safe backfill, history, lifecycle and preservation checks passed"
    )


if __name__ == "__main__":
    check()
