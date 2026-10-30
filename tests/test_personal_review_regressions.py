"""Review regressions must retain prior success and mark every failed attempt stale."""

import json
from http.client import IncompleteRead
from unittest.mock import Mock

import pytest
from test_personal_refresh import inputs
from test_personal_snapshot import api

from film_iq.personal_refresh import refresh


@pytest.mark.parametrize("failure", ["inverse_id_conflict", "incomplete_http"])
def test_rejected_refresh_preserves_success(tmp_path, failure):
    paths = inputs(tmp_path)
    client, snapshot = Mock(), tmp_path / "snapshot.json"
    client.read.return_value = []
    refresh(client, snapshot, **paths)
    previous = snapshot.read_bytes()
    if failure == "inverse_id_conflict":
        client.read.side_effect = [[api(10, 2)], [], [api(20, 2)]]
    else:
        client.read.side_effect = IncompleteRead(b"private partial HTTP payload")
    with pytest.raises(ValueError, match="prior snapshot retained"):
        refresh(client, snapshot, **paths)
    assert snapshot.read_bytes() == previous
    assert json.loads(snapshot.with_suffix(".json.status").read_text()) == {
        "stale": True,
        "error": "refresh_failed",
    }
