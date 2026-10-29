"""Watchlist writes must use the selected movie's confirmed Movary ID."""

import pytest
from conftest import TransportStub

from film_iq.approval import Preview
from film_iq.movary_write import MovaryWriteBackend


def test_watchlist_write_requires_selected_movie_id() -> None:
    transport = TransportStub()
    transport.movie = 456
    backend = MovaryWriteBackend(Preview("Example", 123), "user", transport)
    with pytest.raises(ValueError, match="selected recommendation"):
        backend.add_watchlist(456, approved=True)
    assert transport.calls == []
    assert backend.find_movie(123) == 456
    with pytest.raises(ValueError, match="selected recommendation"):
        backend.add_watchlist(999, approved=True)
    assert all(method != "POST" for method, _, _ in transport.calls)
    backend.add_watchlist(456, approved=True)
    assert transport.calls[-1] == (
        "POST",
        "/api/v1/users/user/watchlist/movies",
        [{"movaryId": 456}],
    )


def test_failed_lookup_clears_prior_confirmation() -> None:
    transport = TransportStub()
    transport.movie = 456
    backend = MovaryWriteBackend(Preview("Example", 123), "user", transport)
    assert backend.find_movie(123) == 456
    with pytest.raises(ValueError):
        backend.find_movie(999)
    with pytest.raises(ValueError, match="selected recommendation"):
        backend.add_watchlist(456, approved=True)
    assert all(method != "POST" for method, _, _ in transport.calls)
