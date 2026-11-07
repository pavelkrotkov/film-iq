"""Exercise the actual watched-refresh CLI and backup with fictional local files."""

import contextlib
import io
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import kaneo_watched_refresh as refresh
from kaneo_watched_refresh_check import fixtures, tracker


def write_private(path: Path, value) -> None:
    path.write_text(json.dumps(value), encoding="utf-8")
    path.chmod(0o600)


def invoke(snapshot: Path, backup: Path | None = None) -> dict:
    args = ["fixture", "--snapshot", str(snapshot)]
    if backup is not None:
        args.extend(["--apply", "--backup", str(backup)])
    out = io.StringIO()
    with (
        patch.object(sys, "argv", args),
        patch.dict(os.environ, {"KANEO_API_KEY": "fictional-key"}),
        patch.object(refresh, "api_key_opener", return_value=object()),
        patch.object(refresh, "call", side_effect=lambda _opener, _base, path: tracker(path)),
        contextlib.redirect_stdout(out),
    ):
        refresh.main()
    assert "fictional-key" not in out.getvalue()
    return json.loads(out.getvalue())


def main() -> None:
    # Test files stay under the selected project, including temporary data.
    root = refresh.ROOT / ".cache/tracker-poc"
    root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="watched-refresh-fictional-", dir=root) as directory:
        project_root = Path(directory)
        private = project_root / "private"
        private.mkdir(mode=0o700)
        sidecar = private / "movary-watched.json"
        snapshot = private / "snapshot.json"
        status = snapshot.with_suffix(".json.status")
        sidecar_data, source, state = fixtures()
        write_private(sidecar, sidecar_data)
        write_private(snapshot, source)
        write_private(status, state)
        write_private(private / "kaneo-private-ids.json", {"project": "fictional-project"})
        original = sidecar.read_bytes()
        with (
            patch.object(refresh, "PROJECT_ROOT", project_root),
            patch.object(refresh, "PRIVATE", private),
            patch.object(refresh, "SIDECAR", sidecar),
        ):
            assert invoke(snapshot) == {"status": "preview", "changed": True}
            assert sidecar.read_bytes() == original
            backup = private / "before.json"
            assert invoke(snapshot, backup) == {"status": "updated"}
            assert backup.read_bytes() == original and backup.stat().st_mode & 0o777 == 0o600
            updated = json.loads(sidecar.read_text())
            assert updated["users"]["other"] == sidecar_data["users"]["other"]
            assert set(updated["users"]["owner"]["films"]) == {"101", "202"}
            assert invoke(snapshot) == {"status": "preview", "changed": False}
            assert invoke(snapshot, private / "unused.json") == {"status": "unchanged"}
            assert not (private / "unused.json").exists()

            # Simulate an intervening writer after the backup is flushed.
            write_private(sidecar, sidecar_data)
            changed = {**sidecar_data, "marker": "fictional-intervening-change"}
            real_fsync = os.fsync

            def concurrent_write(fd):
                real_fsync(fd)
                write_private(sidecar, changed)

            with patch.object(refresh.os, "fsync", side_effect=concurrent_write):
                try:
                    invoke(snapshot, private / "conflict-before.json")
                except ValueError as error:
                    assert "changed" in str(error)
                else:
                    raise AssertionError("Changed sidecar must not be overwritten")
            assert json.loads(sidecar.read_text()) == changed
            assert (private / "conflict-before.json").read_bytes() == original
    print("Fictional CLI preview, backup, apply, owner isolation and changed-state refusal passed")


if __name__ == "__main__":
    main()
