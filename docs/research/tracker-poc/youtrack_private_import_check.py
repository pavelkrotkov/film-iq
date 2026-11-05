"""Exercise idempotence and data minimization with entirely fictional records."""

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
        assert path == "issues" and isinstance(body, dict)
        assert "watched" not in str(body) and "personal_notes" not in str(body)
        self.records.append(
            {"id": str(len(self.records) + 1), "customFields": body["customFields"]}
        )
        if self.lose_response:
            self.lose_response = False
            raise YouTrackError("Simulated lost response after server-side creation")
        return {"id": self.records[-1]["id"]}


def main() -> None:
    film = {
        "tmdb_id": 987654321,
        "title": "Fictional record",
        "source_year": 2001,
        "director": None,
        "watched": True,
        "watched_dates": ["2001-01-01"],
        "personal_notes": "never copied",
        "accepted_discovery_evidence": {"links": []},
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
        assert importer.run(client, [film]) == (0, 1)
        assert len(client.records) == 1
        client.records[0]["summary"] = "Synthetic user edit"
        assert importer.run(client, [film]) == (0, 1)
        assert client.records[0]["summary"] == "Synthetic user edit"
    print("YouTrack private import idempotence and data minimization checks passed")


if __name__ == "__main__":
    main()
