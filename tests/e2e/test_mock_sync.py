"""Synthetic integration seam; the real adapters and API are not connected yet."""

from unittest.mock import Mock, call

import pytest

from film_iq.approval import Preview, approved_movie, sync_one


class StubBackend:
    def __init__(self) -> None:
        self.movies: dict[int, int] = {}
        self.watchlist = {99}
        self.writes: list[tuple[str, int]] = []

    def find_movie(self, tmdb_id: int) -> int | None:
        return self.movies.get(tmdb_id)

    def on_watchlist(self, movie_id: int) -> bool:
        return movie_id in self.watchlist

    def add_movie(self, tmdb_id: int) -> int:
        self.writes.append(("movie", tmdb_id))
        self.movies[tmdb_id] = 456
        return 456

    def add_watchlist(self, movie_id: int) -> None:
        self.writes.append(("watchlist", movie_id))
        self.watchlist.add(movie_id)


def test_mock_source_to_approved_watchlist() -> None:
    source = {"source_id": "poll", "entry_id": "entry-1", "raw_title": "Example", "rank": 1}
    identity = {"entry_id": source["entry_id"], "tmdb_id": 123}
    score = {"entry_id": identity["entry_id"], "significance": 1, "fit": None}
    offer = {"tmdb_id": identity["tmdb_id"], "region": "US", "kind": "free"}
    plan = {"title": source["raw_title"], "tmdb_id": offer["tmdb_id"], "score": score}
    preview = Preview(title=plan["title"], tmdb_id=plan["tmdb_id"])
    writer = Mock()

    with pytest.raises(PermissionError):
        approved_movie(preview)
    with pytest.raises(PermissionError):
        approved_movie(preview, approved=False)
    writer.assert_not_called()
    assert plan["score"]["entry_id"] == source["entry_id"]
    assert (offer["region"], offer["kind"]) == ("US", "free")

    # This fake represents future API behavior, not an actual Movary client.
    movies: dict[int, int] = {}
    watchlist = {99}
    movie_id = approved_movie(preview, approved=True)
    for _ in range(2):
        if movie_id not in movies:
            writer.add_movie(movie_id)
            movies[movie_id] = 456
        if movies[movie_id] not in watchlist:
            writer.add_watchlist(movies[movie_id])
            watchlist.add(movies[movie_id])
    assert writer.mock_calls == [call.add_movie(123), call.add_watchlist(456)]
    assert watchlist == {99, 456}


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


@pytest.mark.parametrize("title,tmdb_id", [("", 1), ("Example", 0), ("Example", True)])
def test_preview_rejects_invalid_identity(title: str, tmdb_id: int) -> None:
    with pytest.raises(ValueError):
        Preview(title, tmdb_id)
