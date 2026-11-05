"""Exercise idempotence and data minimization with entirely fictional records."""

import json
from typing import Any
from unittest.mock import patch

import youtrack_private_import as importer
from youtrack_client import YouTrackClient, YouTrackError


class FakeClient(YouTrackClient):
    def __init__(self) -> None:
        self.records: list[dict[str, Any]] = []
        self.lose_response = False

    def pages(self, path: str, *, query: dict[str, str | int]) -> list[Any]:
        assert path == "issues"
        return self.records.copy()

    def request(
        self,
        path: str,
        *,
        query: dict[str, str | int] | None = None,
        body: dict[str, Any] | None = None,
    ) -> Any:
        if path == "issues" and isinstance(body, dict):
            assert "watched" not in str(body) and "personal_notes" not in str(body)
            fields = body["customFields"].copy()
            for name in ("FilmIQ Source Year", "FilmIQ Director", importer.PROVENANCE_FIELD):
                if not any(field["name"] == name for field in fields):
                    fields.append({"name": name, "value": None})
            self.records.append(
                {
                    "id": str(len(self.records) + 1),
                    "summary": body["summary"],
                    "customFields": fields,
                }
            )
            if self.lose_response:
                self.lose_response = False
                raise YouTrackError("Simulated lost response after server-side creation")
            return {"id": self.records[-1]["id"]}
        record = next(item for item in self.records if path == "issues/" + item["id"])
        if body is not None:
            assert set(body) == {"customFields"} and len(body["customFields"]) == 1
            value = body["customFields"][0]
            assert value["name"] == importer.PROVENANCE_FIELD
            existing = next(
                item for item in record["customFields"] if item["name"] == value["name"]
            )
            assert existing["value"] is None
            existing["value"] = value["value"]
        return record


def main() -> None:
    link = {name: None for name in importer.LINK_FIELDS}
    link.update(
        url="https://example.invalid/list",
        entry_id="synthetic-entry",
        revision_id="synthetic-revision",
    )
    valid_evidence = {"tmdb_id": 987654321, "status": "available", "links": [link]}
    film = {
        "tmdb_id": 987654321,
        "title": "Fictional record",
        "source_year": 2001,
        "director": None,
        "watched": True,
        "watched_dates": ["2001-01-01"],
        "personal_notes": "never copied",
        "field_provenance": {
            "tmdb_id": "Movary API or native export; not independently reverified here",
            "title": "Movary API or native export; upstream catalog origin is unknown",
        },
        "accepted_discovery_evidence": valid_evidence,
    }
    client = FakeClient()
    with (
        patch.object(importer, "ensure_project", return_value="fixture-project"),
        patch.object(importer, "ensure_fields"),
        patch.object(importer, "ensure_lifecycle"),
    ):
        client.lose_response = True
        try:
            importer.run(client, [film])
        except YouTrackError:
            pass
        else:
            raise AssertionError("A lost response must be reported")
        assert importer.run(client, [film]) == (0, 1, 0)
        assert len(client.records) == 1
        client.records[0]["summary"] = "Synthetic user edit"
        source_year = next(
            x for x in client.records[0]["customFields"] if x["name"] == "FilmIQ Source Year"
        )
        source_year["value"] = 2005
        provenance = next(
            x for x in client.records[0]["customFields"] if x["name"] == importer.PROVENANCE_FIELD
        )
        provenance["value"] = None
        assert importer.run(client, [film]) == (0, 1, 1)
        saved = provenance["value"]["text"]
        assert "current value differs from input" in saved
        assert (
            json.loads(saved)["source_year"] == "current value differs from input; origin unknown"
        )
        assert "Movary" not in saved and "watched" not in saved
        provenance["value"] = {"text": "fictional user provenance edit"}
        assert importer.run(client, [film]) == (0, 1, 0)
        assert provenance["value"]["text"] == "fictional user provenance edit"
        assert client.records[0]["summary"] == "Synthetic user edit"
        assert source_year["value"] == 2005
        for evidence in (
            {**valid_evidence, "tmdb_id": 123},
            {
                "tmdb_id": 987654321,
                "status": "unknown",
                "links": [{"url": "https://example.invalid"}],
            },
            {
                **valid_evidence,
                "links": [{**link, "url": "https://user:password@example.invalid/list"}],
            },
            {**valid_evidence, "links": [{**link, "personal_notes": "never copy"}]},
        ):
            invalid = {**film, "accepted_discovery_evidence": evidence}
            try:
                importer.run(client, [invalid])
            except ValueError:
                pass
            else:
                raise AssertionError("Mismatched or malformed evidence was accepted")
        assert len(client.records) == 1
    print("YouTrack private import idempotence and data minimization checks passed")


if __name__ == "__main__":
    main()
