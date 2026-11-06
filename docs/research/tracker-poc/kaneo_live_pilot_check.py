"""Exercise pilot start/restart decisions without touching a running service."""

import hashlib
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import kaneo_live_pilot as pilot


def main() -> None:
    with tempfile.TemporaryDirectory(dir=pilot.ROOT / ".cache/tracker-poc") as directory:
        root = Path(directory)
        pidfile = root / "pilot-pid.json"
        logfile = root / "pilot.log"
        assert pilot.intended_configuration({}, pidfile) == ("pilot", "0", "1")
        pidfile.write_text(
            json.dumps(
                {"pid": 101, "scope": "collection", "tmdb_pace": "1", "tmdb_refresh_enabled": "0"}
            )
        )
        assert pilot.intended_configuration({}, pidfile) == ("collection", "1", "0")
        assert pilot.intended_configuration(
            {"FILMIQ_TMDB_PACE": "0", "FILMIQ_TMDB_REFRESH_ENABLED": "1"}, pidfile, "pilot"
        ) == ("pilot", "0", "1")
        try:
            pilot.intended_configuration({"FILMIQ_TMDB_PACE": "0"}, pidfile, "collection")
        except ValueError:
            pass
        else:
            raise AssertionError("Unpaced collection mode was accepted")

        process = MagicMock(pid=202)
        process.poll.return_value = None
        with (
            patch.object(pilot, "PID_FILE", pidfile),
            patch.object(pilot, "LOG_FILE", logfile),
            patch.object(pilot, "environment", return_value={}),
            patch.object(pilot, "wait_for_listener") as wait,
            patch.object(pilot.os, "kill") as kill,
            patch.object(pilot.subprocess, "Popen", return_value=process) as start,
            patch.object(pilot.subprocess, "check_output") as ps,
            patch.dict(os.environ, {}, clear=True),
        ):
            # A stale PID after reboot must not prevent startup or cause a kill.
            pidfile.write_text(json.dumps({"pid": 101}))
            with patch.object(pilot, "listener", side_effect=[None, 202]):
                pilot.main([])
            assert json.loads(pidfile.read_text())["pid"] == 202
            assert json.loads(pidfile.read_text())["scope"] == "pilot"
            kill.assert_not_called()
            ps.assert_not_called()
            assert wait.call_args_list == [((True,), {})]
            assert start.call_count == 1

            # A running recorded bridge can be restarted.
            wait.reset_mock()
            ps.return_value = f"python {pilot.BRIDGE}\n"
            process.pid = 303
            with patch.object(pilot, "listener", side_effect=[202, 303]):
                pilot.main([])
            kill.assert_called_once_with(202, pilot.signal.SIGTERM)
            assert wait.call_args_list == [((False,), {}), ((True,), {})]
            assert json.loads(pidfile.read_text())["pid"] == 303

            # Start-only never stops or replaces an already running bridge.
            kill.reset_mock()
            start.reset_mock()
            with (
                patch.object(pilot, "environment", side_effect=AssertionError("credentials read")),
                patch.object(pilot, "listener", return_value=303),
            ):
                pilot.main(["--start-only"])
            kill.assert_not_called()
            start.assert_not_called()

            # An unrelated listener is never stopped, even with a stale PID file.
            kill.reset_mock()
            start.reset_mock()
            with patch.object(pilot, "listener", return_value=404):
                try:
                    pilot.main([])
                except RuntimeError:
                    pass
                else:
                    raise AssertionError("Unrecognized listener was accepted")
            kill.assert_not_called()
            start.assert_not_called()

            # Even a matching recycled PID cannot authorize a different command.
            ps.return_value = "unrelated program\n"
            with patch.object(pilot, "listener", return_value=303):
                try:
                    pilot.main([])
                except RuntimeError:
                    pass
                else:
                    raise AssertionError("Unrecognized command was accepted")
            kill.assert_not_called()
            start.assert_not_called()

            # A deliberate collection configuration survives a later restart.
            pidfile.write_text(
                json.dumps(
                    {
                        "pid": 101,
                        "scope": "collection",
                        "tmdb_pace": "1",
                        "tmdb_refresh_enabled": "0",
                    }
                )
            )
            process.pid = 505
            with patch.object(pilot, "listener", side_effect=[None, 505]):
                pilot.main([])
            persisted = json.loads(pidfile.read_text())
            assert (
                persisted["scope"],
                persisted["tmdb_pace"],
                persisted["tmdb_refresh_enabled"],
            ) == ("collection", "1", "0")

            # Explicit pilot mode restores the one-film scope, with explicit flags.
            process.pid = 606
            with (
                patch.dict(
                    os.environ,
                    {"FILMIQ_TMDB_PACE": "0", "FILMIQ_TMDB_REFRESH_ENABLED": "1"},
                    clear=True,
                ),
                patch.object(pilot, "listener", side_effect=[None, 606]),
            ):
                pilot.main(["--pilot"])
            restored = json.loads(pidfile.read_text())
            assert (restored["scope"], restored["tmdb_pace"], restored["tmdb_refresh_enabled"]) == (
                "pilot",
                "0",
                "1",
            )

            # Stop requires no credentials and acts only on the recorded bridge.
            kill.reset_mock()
            wait.reset_mock()
            with (
                patch.object(pilot, "environment", side_effect=AssertionError("credentials read")),
                patch.object(pilot, "listener", return_value=None),
            ):
                pilot.main(["--stop"])
            kill.assert_not_called()
            ps.return_value = f"python {pilot.BRIDGE}\n"
            with (
                patch.object(pilot, "environment", side_effect=AssertionError("credentials read")),
                patch.object(pilot, "listener", return_value=606),
            ):
                pilot.main(["--stop"])
            kill.assert_called_once_with(606, pilot.signal.SIGTERM)
            wait.assert_called_once_with(False)
            kill.reset_mock()
            with patch.object(pilot, "listener", return_value=404):
                try:
                    pilot.main(["--stop"])
                except RuntimeError:
                    pass
                else:
                    raise AssertionError("Stop accepted an unrecognized listener")
            kill.assert_not_called()

        # Synthetic configuration proves the collection uses only the original
        # validated 130-ID approval, with a separate one-film rollback scope.
        fake_root = root / "workspace" / "nested" / "project"
        private = fake_root / ".cache/tracker-poc/private"
        (private / "tmdb-pilot-approval").mkdir(parents=True)
        (private / "tmdb-approval").mkdir()
        (private / "tmdb-live-cache/kaneo/cache").mkdir(parents=True)
        for name in ("policy.json", "authority.json"):
            (private / "tmdb-live-cache/kaneo" / name).write_text("fictional")
        reviewed = (
            fake_root.parent.parent
            / ".cache/epic-c/results/reviewed-display-catalog-expanded-20261031.json"
        )
        reviewed.parent.mkdir(parents=True)
        reviewed.write_text("fictional")
        (private / "youtrack-tmdb-live.env").write_text("TMDB_READ_ACCESS_TOKEN=fictional\n")
        destinations = ["api.themoviedb.org", "image.tmdb.org"]
        (private / "tmdb-pilot-approval/approved-ids.json").write_text(
            json.dumps({"version": 1, "allowed_ids": [1], "destinations": destinations})
        )
        (private / "tmdb-pilot-approval/selection.json").write_text(json.dumps({"tmdb_id": 1}))
        manifest = json.dumps({"films": [{"tmdb_id": item} for item in range(1, 131)]}).encode()
        preview = b"Fictional watched-lookup preview"
        (private / "film-input.json").write_bytes(manifest)
        (private / "tmdb-watched-lookup-preview.md").write_bytes(preview)
        document = {
            "version": 1,
            "allowed_ids": list(range(1, 131)),
            "destinations": destinations,
            "source_manifest_sha256": hashlib.sha256(manifest).hexdigest(),
            "watched_approval_preview_sha256": hashlib.sha256(preview).hexdigest(),
        }
        approved = json.dumps(document).encode()
        (private / "tmdb-approval/approved-ids.json").write_bytes(approved)
        with (
            patch.object(pilot, "ROOT", fake_root),
            patch.object(pilot, "PRIVATE", private),
            patch.dict(os.environ, {}, clear=True),
        ):
            collection = pilot.environment("collection", "1", "0")
            single = pilot.environment("pilot", "0", "1")
        assert collection["FILMIQ_APPROVAL_DIR"] == str(private / "tmdb-approval")
        assert (
            collection["FILMIQ_TMDB_PACE"] == "1"
            and collection["FILMIQ_TMDB_REFRESH_ENABLED"] == "0"
        )
        assert single["FILMIQ_APPROVAL_DIR"] == str(private / "tmdb-pilot-approval")
        assert single["FILMIQ_TMDB_PACE"] == "0" and single["FILMIQ_TMDB_REFRESH_ENABLED"] == "1"
        try:
            pilot.environment("collection", "0", "1")
        except ValueError:
            pass
        else:
            raise AssertionError("Direct configuration allowed unpaced collection mode")
        document["allowed_ids"][-1] = 999
        (private / "tmdb-approval/approved-ids.json").write_text(json.dumps(document))
        with (
            patch.object(pilot, "ROOT", fake_root),
            patch.object(pilot, "PRIVATE", private),
            patch.dict(os.environ, {}, clear=True),
        ):
            try:
                pilot.environment("collection", "1", "1")
            except ValueError:
                pass
            else:
                raise AssertionError("Same-count collection substitution was accepted")
    print("Fictional pilot startup, restart and unrecognized-listener checks passed")


if __name__ == "__main__":
    main()
