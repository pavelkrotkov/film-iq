"""Fictional checks for the offline, new-file-only watchlist initializer."""

import json
import os
import tempfile
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

import kaneo_watchlist_initialize as initializer
from kaneo_watched_refresh import checked_observation
from movary_watchlist_projection_check import fixtures


def rejected(snapshot, status, watched, project_id):
    try:
        initializer.prepare(snapshot, status, watched, project_id)
    except ValueError:
        return
    raise AssertionError("Invalid source/owner/project must not be initialized")


def main():
    snapshot, status = fixtures()
    for film in snapshot["films"]:
        film["watched"] = False
    snapshot["provenance"]["history_csv"] = []
    observation = checked_observation(snapshot, status)
    watched = {
        "version": "tracker-poc-movary-watched-v1",
        "project_id": "fictional1",
        "users": {"userA": observation},
    }
    original = deepcopy((snapshot, status, watched))
    view = initializer.prepare(snapshot, status, watched, "fictional1")
    assert view["users"]["userA"]["entries"][0]["tmdb_id"] == 101
    assert (snapshot, status, watched) == original
    rejected(snapshot, status, watched, "different")
    rejected(snapshot, {**status, "stale": True}, watched, "fictional1")
    rejected(snapshot, status, {**watched, "users": {}}, "fictional1")
    rejected(
        snapshot,
        status,
        {**watched, "users": {"userA": observation, "userB": observation}},
        "fictional1",
    )
    changed = json.loads(json.dumps(watched))
    changed["users"]["userA"]["films"]["999"] = {"watched": True}
    rejected(snapshot, status, changed, "fictional1")

    with tempfile.TemporaryDirectory(dir=".cache/tracker-poc") as name:
        private = Path(name)
        snapshot_file, status_file = private / "snapshot.json", private / "snapshot.json.status"
        watched_file, target = private / "watched.json", private / "new-watchlist.json"
        for path, data in (
            (snapshot_file, snapshot),
            (status_file, status),
            (watched_file, watched),
            (private / "kaneo-private-ids.json", {"project": "fictional1"}),
        ):
            path.write_text(json.dumps(data))
            path.chmod(0o600)
        original_watched = watched_file.read_bytes()
        with patch.multiple(initializer, PRIVATE=private, WATCHED=watched_file, TARGET=target):
            assert initializer.run(snapshot_file) == {"status": "preview", "entries": 1}
            assert not target.exists()
            assert initializer.run(snapshot_file, apply=True) == {"status": "created", "entries": 1}
            assert target.stat().st_uid == os.getuid() and target.stat().st_mode & 0o777 == 0o600
            assert json.loads(target.read_text()) == view
            original_target = target.read_bytes()
            try:
                initializer.run(snapshot_file, apply=True)
            except ValueError:
                pass
            else:
                raise AssertionError("Existing watchlist sidecar must not be overwritten")
            assert target.read_bytes() == original_target
            assert watched_file.read_bytes() == original_watched
    print("Fictional offline watchlist initializer preserves owner, source and existing state")


if __name__ == "__main__":
    main()
