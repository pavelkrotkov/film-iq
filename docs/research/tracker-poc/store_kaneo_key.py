"""Validate and store a separately created Kaneo API key for this local POC.

The key is checked only against the existing POC owner and project using reads.
No browser credentials are used, and a pre-existing key is never overwritten.
"""

import getpass
import json
import os
import stat
import warnings
from pathlib import Path
from urllib.parse import quote

from kaneo_direct_reviews import api_key_opener
from kaneo_smoke import call

ROOT = Path(__file__).resolve().parents[3]
PRIVATE = ROOT / ".cache/tracker-poc/private"
DESTINATION = PRIVATE / "kaneo-api-key"
BASE = "http://localhost:15173"


def private_file(path: Path) -> dict:
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise ValueError("Invalid private input")
    result = json.loads(path.read_text())
    if not isinstance(result, dict):
        raise ValueError("Invalid private input")
    return result


def context(private: Path) -> tuple[str, str]:
    info = private.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise ValueError("Invalid private directory")
    project = private_file(private / "kaneo-private-ids.json").get("project")
    sidecar = private_file(private / "movary-watched.json")
    users = sidecar.get("users")
    if (
        not isinstance(project, str)
        or not project
        or sidecar.get("version") != "tracker-poc-movary-watched-v1"
        or sidecar.get("project_id") != project
        or not isinstance(users, dict)
        or len(users) != 1
    ):
        raise ValueError("Invalid POC identity")
    owner = next(iter(users))
    if not isinstance(owner, str) or not owner:
        raise ValueError("Invalid POC identity")
    return project, owner


def verify(key: str, project: str, owner: str) -> None:
    opener = api_key_opener(key)
    user = call(opener, BASE, "/user/me")
    if not isinstance(user, dict) or user.get("id") != owner:
        raise ValueError("Wrong key owner")
    segment = quote(project, safe="")
    fields = call(opener, BASE, f"/custom-field/project/{segment}")
    if not isinstance(fields, list):
        raise ValueError("Project fields unavailable")
    identity = [
        item for item in fields if isinstance(item, dict) and item.get("name") == "POC TMDB ID"
    ]
    if len(identity) != 1 or identity[0].get("type") != "text":
        raise ValueError("Project identity field unavailable")
    if not isinstance(call(opener, BASE, f"/custom-field/project/{segment}/values"), list):
        raise ValueError("Project values unavailable")
    board = call(opener, BASE, f"/task/tasks/{segment}?limit=100&page=1")
    if not isinstance(board, dict) or not isinstance(board.get("data"), dict):
        raise ValueError("Project tasks unavailable")


def save(key: str, path: Path) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
    fd = os.open(path, flags, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as output:
        output.write(key)


def main() -> None:
    try:
        project, owner = context(PRIVATE)
        if DESTINATION.exists() or DESTINATION.is_symlink():
            raise SystemExit("A Kaneo key already exists; no file was changed.")
        with warnings.catch_warnings():
            warnings.simplefilter("error", getpass.GetPassWarning)
            key = getpass.getpass("Paste the Kaneo POC API key (input is hidden): ")
        verify(key, project, owner)
        save(key, DESTINATION)
    except Exception:
        raise SystemExit(
            "Key storage was not confirmed. Check the local POC, key owner, project access, "
            "and destination file before retrying."
        ) from None
    print("Saved the key privately. Account and project reads passed; write access was not tested.")


if __name__ == "__main__":
    main()
