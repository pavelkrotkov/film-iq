"""Opt-in sync helper checks; all configuration and HTTP are synthetic."""

from unittest.mock import patch

import pytest

from film_iq.sync_cli import sync_watchlist


def test_preview_never_reads_environment_or_network():
    approved = False
    with (
        patch("film_iq.sync_cli.os.environ.get", side_effect=AssertionError("environment")),
        patch("film_iq.movary_http.urlopen", side_effect=AssertionError("network")),
    ):
        assert sync_watchlist("Example", 123, approved=approved) == (
            "Preview: add Example (TMDB 123) to watchlist"
        )


def test_execution_requires_literal_approval_before_config():
    approved = False
    with (
        patch("film_iq.sync_cli.os.environ.get", side_effect=AssertionError("environment")),
        pytest.raises(PermissionError, match="explicit approval"),
    ):
        sync_watchlist("Example", 123, execute=True, approved=approved)


def test_execution_requires_config():
    name, value = "MOVARY_URL", ""
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
