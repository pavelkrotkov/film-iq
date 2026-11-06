"""Export or guardedly restore the current user's full watched property.

Backups contain private watched history. The matching YouTrack app candidate
must be installed before use. Restore assumes a single writer; it does not
claim concurrent compare-and-swap behavior.
"""

import argparse
import json
import os
import stat
from pathlib import Path
from typing import Any

from youtrack_client import ROOT, YouTrackClient

ENDPOINT = "extensionEndpoints/filmiq-poc/movary/"
VERSION = "filmiq-watched-property-export-v1"
PROJECT = ROOT.parent.parent if ROOT.parent.name == ".worktrees" else ROOT


def private_path(value: Path, *, existing: bool) -> Path:
    """Require project-local storage beneath an owner-only directory."""
    path = value.resolve()
    if not path.is_relative_to(PROJECT.resolve()):
        raise ValueError("Backup must be inside the selected project")
    parent = path.parent.stat()
    if not stat.S_ISDIR(parent.st_mode) or parent.st_uid != os.getuid() or parent.st_mode & 0o077:
        raise ValueError("Backup parent must be an owner-only directory")
    if existing:
        info = path.stat()
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
            raise ValueError("Backup must be an owner-only regular file")
    return path


def envelope(value: Any) -> dict:
    if (
        not isinstance(value, dict)
        or set(value) != {"version", "owner", "raw"}
        or value["version"] != VERSION
        or not isinstance(value["owner"], dict)
        or set(value["owner"]) != {"login", "ring_id"}
        or not all(isinstance(item, str) and item for item in value["owner"].values())
        or (value["raw"] is not None and not isinstance(value["raw"], str))
    ):
        raise ValueError("Invalid watched-property backup")
    return value


def current(client: Any) -> dict:
    """Server export validates the complete property and all issue visibility."""
    return envelope(client.request(ENDPOINT + "property-export"))


def export(client: Any, target: Path) -> None:
    path = private_path(target, existing=False)
    data = current(client)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as output:
        json.dump(data, output, ensure_ascii=False)
        output.write("\n")
        output.flush()
        os.fsync(output.fileno())


def restore(client: Any, backup_file: Path, expected_file: Path, *, apply: bool = False) -> str:
    backup = envelope(json.loads(private_path(backup_file, existing=True).read_text()))
    expected = envelope(json.loads(private_path(expected_file, existing=True).read_text()))
    if backup["owner"] != expected["owner"]:
        raise ValueError("Backup and expected export have different owners")
    if current(client) != expected:
        raise ValueError("Current watched property differs from the expected export")
    if not apply:
        return "preview"
    try:
        response = client.request(
            ENDPOINT + "property-restore", body={"expected": expected, "backup": backup}
        )
    except Exception:
        raise RuntimeError("Restore outcome unconfirmed; inspect before retrying") from None
    if not isinstance(response, dict) or response.get("status") not in ("restored", "unchanged"):
        raise RuntimeError("Restore outcome unconfirmed; inspect before retrying")
    try:
        after = current(client)
    except Exception:
        raise RuntimeError("Restore readback unavailable; inspect before retrying") from None
    if after != backup:
        raise RuntimeError("Restore readback differs; inspect before retrying")
    return response["status"]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    output = sub.add_parser("export")
    output.add_argument("path", type=Path)
    recovery = sub.add_parser("restore")
    recovery.add_argument("backup", type=Path)
    recovery.add_argument("--expected", type=Path, required=True)
    recovery.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    client = YouTrackClient()
    if args.action == "export":
        export(client, args.path)
        print('{"status":"exported"}')
    else:
        print(json.dumps({"status": restore(client, args.backup, args.expected, apply=args.apply)}))


if __name__ == "__main__":
    main()
