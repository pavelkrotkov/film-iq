"""Failed and malformed reads preserve the prior private snapshot."""

import json
from unittest.mock import Mock

import pytest
from test_personal_refresh import HEADER, inputs

from film_iq.personal_refresh import refresh


def test_incomplete_or_failed_refresh_preserves_prior_snapshot(tmp_path):
    paths = inputs(tmp_path)
    client, snapshot = Mock(), tmp_path / "snapshot.json"
    client.read.return_value = []
    refresh(client, snapshot, **paths)
    before = snapshot.read_bytes()
    paths["history_csv"].write_text(HEADER + "broken\n")
    with pytest.raises(ValueError, match="prior snapshot retained"):
        refresh(client, snapshot, **paths)
    assert snapshot.read_bytes() == before
    assert json.loads(snapshot.with_suffix(".json.status").read_text())["stale"]
    client.read.side_effect = OSError("private URL and token never in diagnostic")
    with pytest.raises(ValueError, match="Movary refresh failed") as error:
        refresh(client, snapshot, **paths)
    assert "private URL" not in str(error.value)
    assert snapshot.read_bytes() == before
