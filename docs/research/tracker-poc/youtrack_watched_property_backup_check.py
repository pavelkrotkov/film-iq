"""Fictional CLI/handler backup and restore test without network access."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import youtrack_watched_property_backup as backup
from youtrack_watched_refresh import run
from youtrack_watched_refresh_vertical_check import FictionalClient, source


def main() -> None:
    base = backup.ROOT / ".cache/tracker-poc"
    base.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="fictional-watched-backup-", dir=base) as directory:
        root = Path(directory)
        root.chmod(0o700)
        client = FictionalClient()
        try:
            original, expected, wrong_owner = (
                root / name for name in ("original.json", "expected.json", "wrong.json")
            )
            with patch.object(backup, "PROJECT", root):
                backup.export(client, original)
                assert original.stat().st_mode & 0o777 == 0o600
                first = json.loads(original.read_text())
                snapshot, status = source("2026-11-06T12:00:00+00:00")
                assert run(client, snapshot, status, apply=True)["status"] == "imported"
                backup.export(client, expected)
                changed = client.rpc({"action": "raw"})["raw"]
                assert changed != first["raw"]
                assert backup.restore(client, original, expected) == "preview"
                assert client.rpc({"action": "raw"})["raw"] == changed
                try:
                    backup.restore(client, original, original, apply=True)
                except ValueError:
                    pass
                else:
                    raise AssertionError("Stale expected state was accepted")
                different = {**first, "owner": {**first["owner"], "ring_id": "other-fictional"}}
                wrong_owner.write_text(json.dumps(different))
                wrong_owner.chmod(0o600)
                try:
                    backup.restore(client, wrong_owner, expected)
                except ValueError:
                    pass
                else:
                    raise AssertionError("Another user's backup was accepted for preview")
                assert client.rpc({"action": "raw"})["raw"] == changed
                assert backup.restore(client, original, expected, apply=True) == "restored"
                assert client.rpc({"action": "raw"})["raw"] == first["raw"]
                try:
                    backup.export(client, original)
                except FileExistsError:
                    pass
                else:
                    raise AssertionError("Backup overwrote an existing file")
                try:
                    backup.private_path(root.parent / "outside.json", existing=False)
                except ValueError:
                    pass
                else:
                    raise AssertionError("Out-of-project backup path was accepted")
        finally:
            client.close()
    print("Fictional CLI and JS handler preserve full watched property and guard restore")


if __name__ == "__main__":
    main()
