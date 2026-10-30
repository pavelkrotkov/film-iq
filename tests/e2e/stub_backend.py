"""Shared synthetic backend for approval boundary tests."""


class StubBackend:
    def __init__(self) -> None:
        self.movies: dict[int, int] = {}
        self.watchlist = {99}
        self.writes: list[tuple[str, int]] = []

    def find_movie(self, tmdb_id: int) -> int | None:
        return self.movies.get(tmdb_id)

    def on_watchlist(self, movie_id: int) -> bool:
        return movie_id in self.watchlist

    def add_movie(self, tmdb_id: int, *, approved: bool = False) -> int:
        self.writes.append(("movie", tmdb_id))
        self.movies[tmdb_id] = 456
        return 456

    def add_watchlist(self, movie_id: int, *, approved: bool = False) -> None:
        self.writes.append(("watchlist", movie_id))
        self.watchlist.add(movie_id)
