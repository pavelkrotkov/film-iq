"""Check short-page pagination and duplicate detection without credentials."""

from typing import Any

from youtrack_client import YouTrackClient, YouTrackError


class FakeClient(YouTrackClient):
    def __init__(self, pages: list[list[dict[str, str]]]) -> None:
        self.responses = iter(pages)
        self.offsets: list[int] = []

    def request(
        self,
        path: str,
        *,
        query: dict[str, str | int] | None = None,
        body: dict[str, Any] | None = None,
    ) -> Any:
        assert query is not None
        self.offsets.append(int(query["$skip"]))
        return next(self.responses)


def main() -> None:
    client = FakeClient([[{"id": "1"}], [{"id": "2"}], []])
    assert [item["id"] for item in client.pages("issues", query={})] == ["1", "2"]
    assert client.offsets == [0, 1, 2]
    client = FakeClient([[{"id": "1"}], [{"id": "1"}]])
    try:
        client.pages("issues", query={})
    except YouTrackError:
        pass
    else:
        raise AssertionError("Duplicate pages must be rejected")
    print("YouTrack pagination checks passed")


if __name__ == "__main__":
    main()
