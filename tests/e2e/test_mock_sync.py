"""Synthetic integration seam; the real adapters and API are not connected yet."""

from unittest.mock import Mock, call

import pytest

from film_iq.approval import Preview, approved_movie


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


@pytest.mark.parametrize("title,tmdb_id", [("", 1), ("Example", 0), ("Example", True)])
def test_preview_rejects_invalid_identity(title: str, tmdb_id: int) -> None:
    with pytest.raises(ValueError):
        Preview(title, tmdb_id)
