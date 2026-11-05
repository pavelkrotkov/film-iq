"""Supported Movary writes with fresh reads and explicit result verification."""

from film_iq.approval import Preview, sync_one
from film_iq.movary import MovaryClient
from film_iq.movary_http import MovaryHTTPTransport
from film_iq.movary_write import MovaryWriteBackend
from film_iq.personal_identity import api_movies
from film_iq.web_html import title


class MovieActions:
    def __init__(self, item: dict, settings: tuple[str, ...]):
        base, username, token = settings
        self.client = MovaryClient(base, username, token)
        self.transport = MovaryHTTPTransport(base, token)
        self.preview = Preview(title(item), item["tmdb_id"])
        self.backend = MovaryWriteBackend(self.preview, username, self.transport)

    def watchlist(self) -> str:
        result = sync_one(self.preview, self.backend, execute=True, approved=True)
        current = api_movies({"watchlist": self.client.read("watchlist")})
        if self.preview.tmdb_id not in current:
            raise ValueError("Movary watchlist result not verified")
        return result.capitalize() + " in Movary."

    def watched(self, day: str) -> str:
        # Complete API reads are authoritative; cached history cannot justify a write.
        collections = {name: self.client.read(name) for name in ("played", "watchlist")}
        crosswalk = api_movies(collections)
        if recorded(collections["played"], self.preview.tmdb_id, day):
            return "Watch date already recorded in Movary."
        known = crosswalk.get(self.preview.tmdb_id)
        movie = known["movary_id"] if known else self.backend.find_movie(self.preview.tmdb_id)
        if movie is None:
            movie = self.backend.add_movie(self.preview.tmdb_id, approved=True)
        path = self.backend.watchlist.replace("watchlist/movies", "played/movies")
        # PUT upserts only this date. POST would increment plays on retry.
        # Omitted comments preserve existing comments in Movary 0.82.1.
        status, _ = self.transport(
            "PUT", path, [{"movaryId": movie, "watchDates": [{"watchedAt": day, "plays": 1}]}]
        )
        if status != 204 or not recorded(self.client.read("played"), self.preview.tmdb_id, day):
            raise ValueError("Movary watch date result not verified")
        return "Watch date saved in Movary."


def recorded(rows: list[dict], tmdb: int, day: str) -> bool:
    return any(
        date["date"] == day and type(date["plays"]) is int and date["plays"] > 0
        for row in rows
        if row["movie"]["ids"]["tmdb"] == tmdb
        for date in row["watchDates"]
    )
