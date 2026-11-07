"""Preview or initialize one private Kaneo user's Movary watchlist snapshot.

This offline initializer neither queries a tracker nor contacts or changes
Movary. It only creates a new project-local sidecar after the source observation
exactly matches the existing single-owner watched sidecar.
"""

import argparse
import json
from pathlib import Path

from kaneo_watched_refresh import PRIVATE, checked_observation, private_existing
from movary_watchlist_projection import project

from film_iq.personal_io import private_json

WATCHED = PRIVATE / "movary-watched.json"
TARGET = PRIVATE / "movary-watchlist.json"


def prepare(snapshot: dict, status: dict, watched: dict, project_id: str) -> dict:
    observation = checked_observation(snapshot, status)
    if (
        not isinstance(project_id, str)
        or not project_id.isalnum()
        or not isinstance(watched, dict)
        or set(watched) != {"version", "project_id", "users"}
        or watched.get("version") != "tracker-poc-movary-watched-v1"
        or watched.get("project_id") != project_id
        or not isinstance(watched.get("users"), dict)
        or len(watched["users"]) != 1
    ):
        raise ValueError("The existing watched owner and project must be unambiguous")
    user, previous = next(iter(watched["users"].items()))
    if not isinstance(user, str) or not user or previous != observation:
        raise ValueError("The source observation differs from the existing watched sidecar")
    projected = project(snapshot, status, [])
    view = {key: projected[key] for key in ("version", "source", "observed_at", "entries")}
    return {
        "version": "tracker-poc-movary-watchlist-users-v1",
        "project_id": project_id,
        "users": {user: view},
    }


def run(snapshot_file: Path, *, apply: bool = False) -> dict:
    snapshot_file = private_existing(snapshot_file)
    status_file = private_existing(snapshot_file.with_suffix(snapshot_file.suffix + ".status"))
    watched_file = private_existing(WATCHED)
    project_file = private_existing(PRIVATE / "kaneo-private-ids.json")
    originals = {
        path: path.read_bytes() for path in (snapshot_file, status_file, watched_file, project_file)
    }
    snapshot, status, watched, config = (json.loads(originals[path]) for path in originals)
    result = prepare(snapshot, status, watched, config["project"])
    count = len(next(iter(result["users"].values()))["entries"])
    if TARGET.exists():
        raise ValueError("Watchlist sidecar already exists; inspect it before proceeding")
    if not apply:
        return {"status": "preview", "entries": count}
    if any(path.read_bytes() != originals[path] for path in originals):
        raise ValueError("Source changed since preview; inspect before retrying")
    private_json(TARGET, result)
    if json.loads(TARGET.read_text()) != result:
        raise RuntimeError("Watchlist readback differs; inspect before retrying")
    return {"status": "created", "entries": count}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    print(json.dumps(run(args.snapshot, apply=args.apply)))


if __name__ == "__main__":
    main()
