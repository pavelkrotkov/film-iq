"""Credential-free stateful transport for Movary contract tests."""

from urllib.parse import parse_qs, urlsplit


class TransportStub:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, object]] = []
        self.movie: int | None = None
        self.saved = False

    def __call__(self, method: str, path: str, body: object) -> tuple[int, object]:
        self.calls.append((method, path, body))
        url = urlsplit(path)
        if method == "POST" and url.path.endswith("/movies/add"):
            self.movie = 456
            return 200, {"movaryId": 456}
        if method == "POST":
            self.saved = True
            return 204, None
        if url.path.endswith("/movies/search"):
            assert parse_qs(url.query)["search"] == ["Example"]
            return 200, {
                "results": [{"ids": {"tmdb": 123, "movary": self.movie}}],
                "currentPage": 1,
                "maxPage": 1,
            }
        rows = [{"movie": {"ids": {"movary": 456}}}] if self.saved else []
        return 200, {"watchlist": rows, "currentPage": 1, "maxPage": 1}
