"""Exercise existing movie and failed watchlist read behavior."""

from unittest.mock import Mock

import pytest

from film_iq.approval import Preview, sync_one


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


def test_existing_movie_and_failed_read() -> None:
    backend = StubBackend()
    backend.movies[123] = 789
    assert (
        sync_one(Preview("Example", 123), backend, execute=True, approved=True)
        == "added to watchlist"
    )
    assert backend.writes == [("watchlist", 789)]
    backend.on_watchlist = Mock(side_effect=RuntimeError("incomplete read"))
    with pytest.raises(RuntimeError, match="incomplete read"):
        sync_one(Preview("Example", 123), backend, execute=True, approved=True)
    assert backend.writes == [("watchlist", 789)]
