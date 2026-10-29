"""Synthetic integration seam; the real adapters and API are not connected yet."""

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


def test_write_boundary_preview_approval_and_retry() -> None:
    backend = StubBackend()
    preview = Preview("Example", 123)
    assert sync_one(preview, backend) == "Preview: add Example (TMDB 123) to watchlist"
    with pytest.raises(PermissionError):
        sync_one(preview, backend, execute=True)
    assert backend.writes == []
    assert sync_one(preview, backend, execute=True, approved=True) == "added to watchlist"
    assert sync_one(preview, backend, execute=True, approved=True) == "already on watchlist"
    assert backend.writes == [("movie", 123), ("watchlist", 456)]
    assert backend.watchlist == {99, 456}
