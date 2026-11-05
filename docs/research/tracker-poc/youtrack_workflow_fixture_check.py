"""Verify synthetic workflow fixture setup without YouTrack requests."""

from copy import deepcopy
from typing import Any

from youtrack_client import YouTrackClient, YouTrackError
from youtrack_setup import ensure_workflow_fixture


class FakeClient(YouTrackClient):
    def __init__(self, target: Any = None, other: Any = 1) -> None:
        self.rows: list[dict[str, Any]] = [
            {
                "id": "a",
                "idReadable": "FILMPOC-1",
                "customFields": [
                    {"name": "FilmIQ Fixture ID", "value": target},
                    {"name": "Unrelated", "value": "untouched"},
                ],
            },
            {
                "id": "b",
                "idReadable": "FILMPOC-2",
                "customFields": [{"name": "FilmIQ Fixture ID", "value": other}],
            },
        ]
        self.writes = 0

    def pages(self, path: str, *, query: dict[str, str | int]) -> list[Any]:
        assert path == "issues" and "FILMPOC" in str(query["query"])
        return deepcopy(self.rows)

    def request(
        self,
        path: str,
        *,
        query: dict[str, str | int] | None = None,
        body: dict[str, Any] | None = None,
    ) -> Any:
        assert path == "issues/FILMPOC-1"
        if body is not None:
            self.writes += 1
            assert body == {
                "customFields": [
                    {"name": "FilmIQ Fixture ID", "$type": "SimpleIssueCustomField", "value": 91001}
                ]
            }
            self.rows[0]["customFields"][0]["value"] = 91001
        return deepcopy(self.rows[0])


def run() -> None:
    client = FakeClient()
    assert ensure_workflow_fixture(client) is True
    assert ensure_workflow_fixture(client) is False and client.writes == 1
    assert client.rows[0]["customFields"][1]["value"] == "untouched"
    for bad in (FakeClient(target=7), FakeClient(target=True), FakeClient(other=91001)):
        try:
            ensure_workflow_fixture(bad)
        except YouTrackError:
            assert bad.writes == 0
        else:
            raise AssertionError("Ambiguous or edited fixture accepted")
    print("Synthetic workflow fixture creation, retry and conflict checks passed")


if __name__ == "__main__":
    run()
