"""Check offline watchlist refresh with only fictional files and source data."""

import json
import os
import tempfile
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

import kaneo_watchlist_initialize as initializer
import kaneo_watchlist_refresh as refresh
from kaneo_watched_refresh import checked_observation
from movary_watchlist_projection_check import fixtures


def reject(fn):
    try:
        fn()
    except (ValueError, FileExistsError):
        return
    raise AssertionError("Invalid fictional refresh must be rejected")


def main():
    old, old_status = fixtures()
    for film in old["films"]:
        film["watched"] = False
    old["provenance"]["history_csv"] = []
    old_watched: dict = {
        "version": "tracker-poc-movary-watched-v1",
        "project_id": "fictional1",
        "users": {"owner": checked_observation(old, old_status)},
    }
    existing = initializer.prepare(old, old_status, old_watched, "fictional1")
    existing["users"]["other"] = deepcopy(existing["users"]["owner"])
    new = deepcopy(old)
    new["last_successful_refresh"] = "2026-11-07T12:34:56+00:00"
    new["films"][0]["watchlist"] = False
    new["films"][1]["watchlist"] = True
    new["provenance"]["api"]["watchlist"] = [
        {"movie": {"ids": {"tmdb": 102, "movary": 502}, "title": "Other"}, "addedAt": None}
    ]
    status = {"stale": False, "last_successful_refresh": new["last_successful_refresh"]}
    watched = deepcopy(old_watched)
    watched["users"]["owner"] = checked_observation(new, status)
    original = deepcopy((new, status, watched, existing))
    result = refresh.prepare(new, status, watched, "fictional1", existing)
    assert result["users"]["owner"]["entries"][0]["tmdb_id"] == 102
    assert result["users"]["other"] == existing["users"]["other"]
    assert (new, status, watched, existing) == original
    assert refresh.prepare(old, old_status, old_watched, "fictional1", existing) == existing
    reject(lambda: refresh.prepare(new, {**status, "stale": True}, watched, "fictional1", existing))
    reject(lambda: refresh.prepare(new, status, old_watched, "fictional1", existing))
    reject(lambda: refresh.prepare(new, status, watched, "wrong", existing))
    reject(lambda: refresh.prepare(old, old_status, old_watched, "fictional1", result))
    conflict = deepcopy(existing)
    conflict["users"]["owner"]["entries"][0]["title"] = "Different"
    reject(lambda: refresh.prepare(old, old_status, old_watched, "fictional1", conflict))
    incomplete = deepcopy(new)
    del incomplete["provenance"]["api"]["watchlist"]
    reject(lambda: refresh.prepare(incomplete, status, watched, "fictional1", existing))
    disagreement = deepcopy(new)
    disagreement["films"][1]["watchlist"] = False
    reject(lambda: refresh.prepare(disagreement, status, watched, "fictional1", existing))
    missing_owner = {**existing, "users": {"other": existing["users"]["other"]}}
    reject(lambda: refresh.prepare(new, status, watched, "fictional1", missing_owner))

    with tempfile.TemporaryDirectory(dir=".cache/tracker-poc") as name:
        private = Path(name)
        source, marker = private / "snapshot.json", private / "snapshot.json.status"
        watched_file, target = private / "watched.json", private / "watchlist.json"
        for path, data in (
            (source, new),
            (marker, status),
            (watched_file, watched),
            (target, existing),
            (private / "kaneo-private-ids.json", {"project": "fictional1"}),
        ):
            path.write_text(json.dumps(data))
            path.chmod(0o600)
        prior_bytes = target.read_bytes()
        watched_bytes = watched_file.read_bytes()
        with patch.multiple(initializer, PRIVATE=private, WATCHED=watched_file, TARGET=target):
            preview = refresh.run(source)
            assert preview["status"] == "preview" and preview["added"] == 1
            assert preview["no_longer_observed"] == 1 and target.read_bytes() == prior_bytes
            reject(lambda: refresh.run(source, apply=True))
            used = private / "used-backup.json"
            used.write_text("existing")
            reject(lambda: refresh.run(source, apply=True, backup=used))
            assert used.read_text() == "existing" and target.read_bytes() == prior_bytes
            mutation_backup = private / "mutation-backup.json"
            check_private = refresh.private_existing

            def mutate_input(path):
                result_path = check_private(path)
                if path == mutation_backup.resolve():
                    marker.write_text("{}")
                return result_path

            with patch.object(refresh, "private_existing", side_effect=mutate_input):
                reject(lambda: refresh.run(source, apply=True, backup=mutation_backup))
            assert (
                mutation_backup.read_bytes() == prior_bytes and target.read_bytes() == prior_bytes
            )
            marker.write_text(json.dumps(status))
            backup = private / "backup.json"
            assert refresh.run(source, apply=True, backup=backup)["status"] == "updated"
            assert backup.read_bytes() == prior_bytes
            assert backup.stat().st_uid == os.getuid() and backup.stat().st_mode & 0o777 == 0o600
            assert (
                json.loads(target.read_text()) == result
                and watched_file.read_bytes() == watched_bytes
            )
            assert refresh.run(source, apply=True)["status"] == "unchanged"
    print("Fictional watchlist refresh preserves scope, checks freshness and creates exact backup")


if __name__ == "__main__":
    main()
