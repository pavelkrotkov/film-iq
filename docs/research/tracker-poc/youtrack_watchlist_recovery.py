"""Export or restore the authenticated user's complete watchlist property.

Backups are private. Restore is preview-first and assumes one writer; the
server's expected-value check is not a proven atomic compare-and-swap.
"""

import argparse
import json
import os
from pathlib import Path
from typing import Any

from youtrack_client import YouTrackClient
from youtrack_watched_property_backup import private_path
from youtrack_watchlist_import import ENDPOINT, current, envelope


def export(client: Any, target: Path) -> None:
    path = private_path(target, existing=False)
    value = current(client)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as output:
        json.dump(value, output, ensure_ascii=False)
        output.write("\n")
        output.flush()
        os.fsync(output.fileno())
    if envelope(json.loads(path.read_text())) != value:
        raise RuntimeError("Watchlist backup could not be verified")


def restore(client: Any, backup_path: Path, expected_path: Path, *, apply: bool = False) -> str:
    saved = envelope(json.loads(private_path(backup_path, existing=True).read_text()))
    expected = envelope(json.loads(private_path(expected_path, existing=True).read_text()))
    if saved["owner"] != expected["owner"] or current(client) != expected:
        raise ValueError("Owner or current property does not match expected export")
    if not apply:
        return "preview"
    try:
        result = client.request(
            ENDPOINT + "property-restore", body={"backup": saved, "expected": expected}
        )
        if not isinstance(result, dict) or result.get("status") not in ("restored", "unchanged"):
            raise ValueError("Unexpected restore response")
        if current(client) != saved:
            raise ValueError("Restore readback differs")
    except Exception:
        raise RuntimeError("Restore outcome unconfirmed; inspect before retrying") from None
    return result["status"]


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
