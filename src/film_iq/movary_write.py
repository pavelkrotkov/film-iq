"""Movary 0.82.1 write adapter for one selected recommendation.

The caller supplies an authenticated transport that returns a status and decoded
JSON. All requests are explicit; no transport, credentials, or live instance is
configured by this module. Use the approval boundary to execute writes. The
search must return the selected TMDB ID before absence can be established, and
every page must be fetched successfully. A failed request is never absence.
The installed instance's version and behavior still need independent checking.
"""

from collections.abc import Callable
from urllib.parse import quote

from film_iq.approval import Preview
from film_iq.movary_pages import object_data as _object
from film_iq.movary_pages import pages

Transport = Callable[[str, str, object], tuple[int, object]]


def _id(value: object) -> int:
    if type(value) is not int or value < 1:
        raise ValueError("Invalid Movary or TMDB ID")
    return value


class MovaryWriteBackend:
    """Use only through sync_one; the transport performs HTTP and authentication."""

    def __init__(self, preview: Preview, username: str, transport: Transport):
        if not username.strip():
            raise ValueError("username is required")
        self.preview = preview
        self.transport = transport
        self._movie_id: int | None = None
        self.watchlist = f"/api/v1/users/{quote(username, safe='')}/watchlist/movies"

    def _request(
        self, method: str, path: str, body: object, expected: int, *, approved: bool = False
    ) -> object:
        if method == "POST" and approved is not True:
            raise PermissionError("explicit approval is required for a Movary write")
        status, response = self.transport(method, path, body)
        if status != expected:
            raise ValueError(f"Movary HTTP status {status}; expected {expected}")
        return response

    def _pages(self, path: str, key: str, params: dict[str, str | int]) -> list:
        return pages(lambda url: self._request("GET", url, None, 200), path, key, params)

    def find_movie(self, tmdb_id: int) -> int | None:
        self._movie_id = None
        if tmdb_id != self.preview.tmdb_id:
            raise ValueError("Selected recommendation does not match")
        rows = self._pages("/api/v1/movies/search", "results", {"search": self.preview.title})
        matches = []
        for row in rows:
            ids = _object(_object(row).get("ids"))
            if _id(ids.get("tmdb")) == tmdb_id:
                if "movary" not in ids:
                    raise ValueError("Missing Movary ID in search result")
                matches.append(ids.get("movary"))
        if len(matches) != 1:
            raise ValueError("Selected TMDB ID missing or ambiguous in complete search")
        self._movie_id = None if matches[0] is None else _id(matches[0])
        return self._movie_id

    def on_watchlist(self, movie_id: int) -> bool:
        rows = self._pages(self.watchlist, "watchlist", {"limit": 100})
        ids = [
            _id(_object(_object(_object(row).get("movie")).get("ids")).get("movary"))
            for row in rows
        ]
        return movie_id in ids

    def add_movie(self, tmdb_id: int, *, approved: bool = False) -> int:
        if tmdb_id != self.preview.tmdb_id:
            raise ValueError("Selected recommendation does not match")
        self._movie_id = None
        data = self._request(
            "POST", "/api/v1/movies/add", {"tmdbId": tmdb_id}, 200, approved=approved
        )
        self._movie_id = _id(_object(data).get("movaryId"))
        return self._movie_id

    def add_watchlist(self, movie_id: int, *, approved: bool = False) -> None:
        if approved is not True:
            raise PermissionError("explicit approval is required for a Movary write")
        if self._movie_id is None or type(movie_id) is not int or movie_id != self._movie_id:
            raise ValueError("Movary ID does not match the selected recommendation")
        self._request("POST", self.watchlist, [{"movaryId": movie_id}], 204, approved=approved)
