"""Exercise existing movie and failed watchlist read behavior."""

from unittest.mock import Mock

import pytest
from stub_backend import StubBackend

from film_iq.approval import Preview, sync_one


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
