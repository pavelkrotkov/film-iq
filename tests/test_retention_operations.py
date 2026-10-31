"""Disposable-cache dry-run and termination/expiry simulation; no live deletion."""

from datetime import UTC, datetime, timedelta

import pytest

from film_iq.cache_purge import purge
from film_iq.retention import CachePolicy, status

NOW = datetime(2026, 10, 30, tzinfo=UTC)


def policy(**kwargs):
    return CachePolicy(
        "synthetic", rights_evidence="explicit fixture permission", attribution="test", **kwargs
    )


def test_unresolved_rights_block_retention_and_paths_cannot_escape(tmp_path):
    blocked = policy(allowed=False, expires_at=NOW + timedelta(days=1))
    assert status(blocked, NOW) == "blocked"
    assert purge(tmp_path, ["missing"], blocked, NOW) == ()
    with pytest.raises(ValueError, match="inside"):
        purge(tmp_path, ["../original.csv"], blocked, NOW, execute=True)
    with pytest.raises(ValueError, match="timezone"):
        status(blocked, datetime(2026, 10, 30))
