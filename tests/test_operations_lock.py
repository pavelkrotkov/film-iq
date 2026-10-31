"""A scheduled overlap must not start a second refresh or replace status."""

import fcntl
from unittest.mock import Mock

import pytest
from operations_support import configuration

from film_iq import operations_run


def test_overlap_does_not_refresh_or_replace_status(tmp_path, monkeypatch):
    refresh, paths = configuration(tmp_path, monkeypatch)
    lock_path = paths["status"].with_suffix(".status.lock")
    with lock_path.open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(BlockingIOError):
            operations_run.run_once(Mock(), **paths)
    refresh.assert_not_called()
    assert not paths["status"].exists()
