"""Preview or manually refresh a Kaneo Movary watchlist projection offline.

First refresh the existing watched sidecar to the same complete observation.
Apply requires a new owner-only backup and a single writer. This tool does not
contact Movary, a tracker, browser sessions or metadata providers.
"""

import argparse
import json
import os
import stat
from datetime import datetime
from pathlib import Path

import kaneo_watchlist_initialize as initializer
from kaneo_watched_refresh import PROJECT_ROOT, private_existing
from movary_watchlist_projection import validate_view

from film_iq.personal_io import private_json


def prepare(snapshot: dict, status: dict, watched: dict, project_id: str, existing: dict) -> dict:
    """Replace only the existing watched owner's view from the same complete source."""
    projected = initializer.prepare(snapshot, status, watched, project_id)
    owner, new = next(iter(projected["users"].items()))
    if (
        not isinstance(existing, dict)
        or set(existing) != {"version", "project_id", "users"}
        or existing.get("version") != "tracker-poc-movary-watchlist-users-v1"
        or existing.get("project_id") != project_id
        or not isinstance(existing.get("users"), dict)
        or owner not in existing["users"]
    ):
        raise ValueError("Existing watchlist owner and project must match")
    previous = validate_view(existing["users"][owner])
    old_at = datetime.fromisoformat(previous["observed_at"])
    new_at = datetime.fromisoformat(new["observed_at"])
    if new_at < old_at or (new_at == old_at and new != previous):
        raise ValueError("Watchlist observation is older or conflicts at the same time")
    return {**existing, "users": {**existing["users"], owner: new}}


def run(snapshot_file: Path, *, apply: bool = False, backup: Path | None = None) -> dict:
    snapshot_file = private_existing(snapshot_file)
    status_file = private_existing(snapshot_file.with_suffix(snapshot_file.suffix + ".status"))
    watched_file = private_existing(initializer.WATCHED)
    project_file = private_existing(initializer.PRIVATE / "kaneo-private-ids.json")
    target = private_existing(initializer.TARGET)
    originals = {
        path: path.read_bytes()
        for path in (snapshot_file, status_file, watched_file, project_file, target)
    }
    snapshot, status, watched, config, existing = (
        json.loads(originals[path]) for path in originals
    )
    result = prepare(snapshot, status, watched, config["project"], existing)
    owner = next(iter(watched["users"]))
    before = existing["users"][owner]
    after = result["users"][owner]
    previous_ids = {entry["tmdb_id"] for entry in before["entries"]}
    next_ids = {entry["tmdb_id"] for entry in after["entries"]}
    preview = {
        "changed": result != existing,
        "observed_at": after["observed_at"],
        "previous_observed_at": before["observed_at"],
        "added": len(next_ids - previous_ids),
        "no_longer_observed": len(previous_ids - next_ids),
    }
    if not apply:
        return {"status": "preview", **preview}
    if any(path.read_bytes() != originals[path] for path in originals):
        raise ValueError("An input changed; inspect and preview again")
    if result == existing:
        return {"status": "unchanged", **preview}
    if backup is None:
        raise ValueError("A new owner-only backup path is required")
    parent = backup.parent.resolve(strict=True)
    info = parent.stat()
    if (
        not parent.is_relative_to(PROJECT_ROOT.resolve())
        or not stat.S_ISDIR(info.st_mode)
        or info.st_uid != os.getuid()
        or info.st_mode & 0o077
    ):
        raise ValueError("Backup directory must be owner-only and inside the project")
    backup_file = parent / backup.name
    fd = os.open(backup_file, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as output:
        output.write(originals[target])
        output.flush()
        os.fsync(output.fileno())
    if private_existing(backup_file).read_bytes() != originals[target]:
        raise ValueError("Backup readback differs")
    if any(path.read_bytes() != originals[path] for path in originals):
        raise ValueError("An input changed; inspect backup and preview again")
    private_json(target, result)
    if json.loads(target.read_text()) != result:
        raise RuntimeError("Watchlist readback differs; inspect before retrying")
    return {"status": "updated", **preview}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--backup", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    print(json.dumps(run(args.snapshot, apply=args.apply, backup=args.backup)))


if __name__ == "__main__":
    main()
