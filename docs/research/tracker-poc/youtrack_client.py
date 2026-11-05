"""Small YouTrack REST client for the loopback-only tracker experiment."""

import json
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener

ROOT = Path(__file__).resolve().parents[3]
TOKEN_PATH = ROOT / ".cache/tracker-poc/private/youtrack-token"
BASE_URL = "http://localhost:18180/api/"


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(
        self, req: Any, fp: Any, code: Any, msg: Any, headers: Any, newurl: Any
    ) -> None:
        return None


class YouTrackError(RuntimeError):
    """A local request failed without exposing a credential or private response."""


class YouTrackClient:
    def __init__(self, token_path: Path = TOKEN_PATH) -> None:
        self._token = token_path.read_text(encoding="utf-8").strip()
        if not self._token or "\n" in self._token or "\r" in self._token:
            raise ValueError("The local YouTrack token is empty or malformed")
        self._opener = build_opener(NoRedirect())

    def request(
        self,
        path: str,
        *,
        query: dict[str, str | int] | None = None,
        body: dict[str, Any] | None = None,
    ) -> Any:
        if not path or path.startswith("/") or ".." in path or "://" in path:
            raise ValueError("Expected a relative YouTrack API path")
        url = BASE_URL + path
        if query:
            url += "?" + urlencode(query)
        request = Request(
            url,
            data=json.dumps(body).encode() if body is not None else None,
            headers={
                "Authorization": f"Bearer {self._token}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            method="POST" if body is not None else "GET",
        )
        try:
            with self._opener.open(request, timeout=30) as response:
                data = response.read()
        except HTTPError as exc:
            raise YouTrackError(
                f"YouTrack {request.method} {path} returned HTTP {exc.code}"
            ) from None
        except (URLError, TimeoutError, OSError) as exc:
            raise YouTrackError(f"YouTrack {request.method} {path} could not be reached") from exc
        try:
            return json.loads(data) if data else None
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise YouTrackError(f"YouTrack {request.method} {path} returned invalid JSON") from exc

    def pages(self, path: str, *, query: dict[str, str | int]) -> list[Any]:
        """Read every page, including servers that cap page sizes below $top."""
        records: list[Any] = []
        seen: set[str] = set()
        while True:
            page = self.request(path, query={**query, "$top": 100, "$skip": len(records)})
            if not isinstance(page, list):
                raise YouTrackError("Expected a paginated list")
            if not page:
                return records
            for row in page:
                if not isinstance(row, dict) or not isinstance(row.get("id"), str):
                    raise YouTrackError("Pagination returned a record without an ID")
                if row["id"] in seen:
                    raise YouTrackError("Pagination returned duplicate IDs; retry the read")
                seen.add(row["id"])
            records.extend(page)
