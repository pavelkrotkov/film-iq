"""Preview or refresh the Kaneo user's Movary sidecar using an independent API key.

The supplied snapshot must be a complete local Movary observation. This tool
does not access Movary, browser sessions, tracker fields, or editable preferences
for writing. A separate mode-0600 backup is required before applying.
"""

import argparse
import json
import os
import stat
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import quote, urlsplit

from kaneo_direct_reviews import api_key_opener
from kaneo_movary_mapping import mapping, merge
from kaneo_smoke import call

from film_iq.personal_identity import api_movies, index
from film_iq.personal_io import private_json

ROOT = Path(__file__).resolve().parents[3]
PROJECT_ROOT = ROOT.parent.parent if ROOT.parent.name == ".worktrees" else ROOT
PRIVATE = ROOT / ".cache/tracker-poc/private"
SIDECAR = PRIVATE / "movary-watched.json"
IDENTITY = "POC TMDB ID"


def checked_observation(snapshot: dict, status: dict) -> dict:
    """Require the complete source collections to agree on watched membership."""
    provenance = snapshot.get("provenance")
    if not isinstance(provenance, dict) or not isinstance(provenance.get("api"), dict):
        raise ValueError("Complete Movary provenance is required")
    api = provenance["api"]
    if not all(isinstance(api.get(name), list) for name in ("played", "history", "watchlist")):
        raise ValueError("Complete Movary API collections are required")
    if not isinstance(provenance.get("history_csv"), list):
        raise ValueError("Complete Movary history export is required")
    observation = mapping(snapshot, status)
    if observation["unresolved_history"]:
        raise ValueError("Unresolved watched history requires review")
    movies = api_movies(api)
    expected = {
        ident for ident, record in movies.items() if record.get("played") or record.get("history")
    } | set(index(provenance["history_csv"]))
    if {int(ident) for ident in observation["films"]} != expected:
        raise ValueError("Watched observation disagrees with source provenance")
    return observation


def prepare(opener, base: str, project: str, existing: dict, snapshot: dict, status: dict) -> dict:
    """Verify key owner, complete source and current unique project mappings."""
    observation = checked_observation(snapshot, status)
    user = call(opener, base, "/user/me")
    user_id = user.get("id") if isinstance(user, dict) else None
    if not isinstance(user_id, str) or not user_id:
        raise ValueError("API-key owner is unavailable")
    if not isinstance(existing.get("users"), dict) or user_id not in existing["users"]:
        raise ValueError("API-key owner does not have a watched sidecar")
    segment = quote(project, safe="")
    definitions = call(opener, base, f"/custom-field/project/{segment}")
    fields = [field for field in definitions if field.get("name") == IDENTITY]
    if len(fields) != 1 or fields[0].get("type") != "text":
        raise ValueError("Project identity field is unavailable or ambiguous")
    field_id = fields[0]["id"]
    values = call(opener, base, f"/custom-field/project/{segment}/values")
    found = {}
    for row in values:
        if row.get("fieldId") != field_id or not row.get("value"):
            continue
        ident, task = row["value"], row.get("taskId")
        if (
            not isinstance(ident, str)
            or not ident.isascii()
            or not ident.isdigit()
            or str(int(ident)) != ident
            or int(ident) <= 0
            or not isinstance(task, str)
            or not task
            or ident in found
            or task in found.values()
        ):
            raise ValueError("Project film identities are invalid or duplicated")
        found[ident] = task
    if not set(observation["films"]).issubset(found):
        raise ValueError("A watched film has no unique project record")
    for ident in observation["films"]:
        task = found[ident]
        task_segment = quote(task, safe="")
        record = call(opener, base, f"/task/{task_segment}")
        rows = call(opener, base, f"/custom-field/task/{task_segment}")
        matching = [row.get("value") for row in rows if row.get("fieldId") == field_id]
        if record.get("id") != task or matching != [ident]:
            raise ValueError("A watched film mapping changed or is inaccessible")
    prior = existing["users"][user_id]
    if (
        not isinstance(prior, dict)
        or set(prior) != {"source", "observed_at", "films", "unresolved_history"}
        or prior.get("unresolved_history")
    ):
        raise ValueError("Existing unresolved watched history requires review")
    result = merge(existing, project, user_id, observation)
    old_at = datetime.fromisoformat(prior["observed_at"])
    new_at = datetime.fromisoformat(observation["observed_at"])
    if old_at == new_at and prior != observation:
        raise ValueError("The same source observation differs from the stored sidecar")
    return result


def private_existing(path: Path) -> Path:
    path = path.resolve(strict=True)
    info = path.stat()
    if (
        not path.is_relative_to(PROJECT_ROOT.resolve())
        or not stat.S_ISREG(info.st_mode)
        or info.st_uid != os.getuid()
        or info.st_mode & 0o077
    ):
        raise ValueError("Input must be an owner-only project file")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--base", default="http://localhost:15173")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--backup", type=Path)
    args = parser.parse_args()
    base = urlsplit(args.base)
    if base.scheme != "http" or base.hostname not in ("localhost", "127.0.0.1"):
        raise ValueError("Only local Kaneo is supported")
    snapshot = private_existing(args.snapshot)
    status = private_existing(snapshot.with_suffix(snapshot.suffix + ".status"))
    target = private_existing(SIDECAR)
    original = target.read_bytes()
    existing = json.loads(original)
    project = json.loads(private_existing(PRIVATE / "kaneo-private-ids.json").read_text())[
        "project"
    ]
    result = prepare(
        api_key_opener(os.environ.get("KANEO_API_KEY")),
        args.base.rstrip("/"),
        project,
        existing,
        json.loads(snapshot.read_text()),
        json.loads(status.read_text()),
    )
    if not args.apply:
        print(json.dumps({"status": "preview", "changed": result != existing}))
        return
    if result == existing:
        if target.read_bytes() != original:
            raise ValueError("Sidecar changed since preview; inspect before retrying")
        print(json.dumps({"status": "unchanged"}))
        return
    if args.backup is None:
        raise ValueError("A new owner-only backup path is required for apply")
    parent = args.backup.parent.resolve(strict=True)
    info = parent.stat()
    if (
        not parent.is_relative_to(PROJECT_ROOT.resolve())
        or info.st_uid != os.getuid()
        or info.st_mode & 0o077
    ):
        raise ValueError("Backup directory must be owner-only and inside the project")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
    fd = os.open(parent / args.backup.name, flags, 0o600)
    with os.fdopen(fd, "wb") as backup:
        backup.write(original)
        backup.flush()
        os.fsync(backup.fileno())
    if target.read_bytes() != original:
        raise ValueError("Sidecar changed since preview; inspect before retrying")
    private_json(target, result)
    if json.loads(target.read_text()) != result:
        raise RuntimeError("Sidecar readback differs; inspect before retrying")
    print(json.dumps({"status": "updated" if result != existing else "unchanged"}))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print(
            "Watched refresh was not confirmed; inspect inputs and sidecar before retrying.",
            file=sys.stderr,
        )
        raise SystemExit(1) from None
