"""Opt-in sync helper checks; all configuration and HTTP are synthetic."""

from unittest.mock import patch

import pytest

from film_iq.sync_cli import sync_watchlist


@pytest.mark.parametrize("approved", [False, True, 1, "yes"])
def test_preview_never_reads_environment_or_network(approved):
    with (
        patch("film_iq.sync_cli.os.environ.get", side_effect=AssertionError("environment")),
        patch("film_iq.movary_http.urlopen", side_effect=AssertionError("network")),
    ):
        assert sync_watchlist("Example", 123, approved=approved) == (
            "Preview: add Example (TMDB 123) to watchlist"
        )


@pytest.mark.parametrize("approved", [False, 1, "yes", None])
def test_execution_requires_literal_approval_before_config(approved):
    with (
        patch("film_iq.sync_cli.os.environ.get", side_effect=AssertionError("environment")),
        pytest.raises(PermissionError, match="explicit approval"),
    ):
        sync_watchlist("Example", 123, execute=True, approved=approved)


@pytest.mark.parametrize("name", ["MOVARY_URL", "MOVARY_USERNAME", "MOVARY_TOKEN"])
@pytest.mark.parametrize("value", ["", "   "])
def test_execution_requires_config(name, value):
    config = dict(
        MOVARY_URL="https://movary.invalid",
        MOVARY_USERNAME="example",
        MOVARY_TOKEN="test-placeholder",
    )
    config[name] = value
    with (
        patch.dict("os.environ", config, clear=True),
        patch("film_iq.movary_http.urlopen", side_effect=AssertionError("network")),
        pytest.raises(ValueError, match=name),
    ):
        sync_watchlist("Example", 123, execute=True, approved=True)


def test_execution_uses_existing_backend_and_sync():
    config = dict(
        MOVARY_URL="https://movary.invalid",
        MOVARY_USERNAME="example",
        MOVARY_TOKEN="test-placeholder",
    )
    replies = [
        (
            200,
            {"results": [{"ids": {"tmdb": 123, "movary": None}}], "currentPage": 1, "maxPage": 1},
        ),
        (200, {"movaryId": 456}),
        (200, {"watchlist": [], "currentPage": 1, "maxPage": 1}),
        (204, None),
    ]
    with (
        patch.dict("os.environ", config, clear=True),
        patch("film_iq.sync_cli.MovaryHTTPTransport", autospec=True) as transport,
    ):
        transport.return_value.side_effect = replies
        assert sync_watchlist("Example", 123, execute=True, approved=True) == "added to watchlist"
        transport.assert_called_once_with(config["MOVARY_URL"], config["MOVARY_TOKEN"])
        assert [call.args[0] for call in transport.return_value.call_args_list] == [
            "GET",
            "POST",
            "GET",
            "POST",
        ]


@pytest.mark.parametrize("title, tmdb_id", [("", 123), ("Example", 0), ("Example", True)])
def test_invalid_selection(title, tmdb_id):
    with pytest.raises(ValueError, match="title and positive"):
        sync_watchlist(title, tmdb_id)
