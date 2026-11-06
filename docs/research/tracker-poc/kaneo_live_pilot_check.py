"""Exercise pilot start/restart decisions without touching a running service."""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import kaneo_live_pilot as pilot


def main() -> None:
    with tempfile.TemporaryDirectory(dir=pilot.ROOT / ".cache/tracker-poc") as directory:
        root = Path(directory)
        pidfile = root / "pilot-pid.json"
        logfile = root / "pilot.log"
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
        ):
            # A stale PID after reboot must not prevent startup or cause a kill.
            pidfile.write_text(json.dumps({"pid": 101}))
            with patch.object(pilot, "listener", side_effect=[None, 202]):
                pilot.main()
            assert json.loads(pidfile.read_text())["pid"] == 202
            kill.assert_not_called()
            ps.assert_not_called()
            assert wait.call_args_list == [((True,), {})]
            assert start.call_count == 1

            # A running recorded bridge can be restarted.
            wait.reset_mock()
            ps.return_value = f"python {pilot.BRIDGE}\n"
            process.pid = 303
            with patch.object(pilot, "listener", side_effect=[202, 303]):
                pilot.main()
            kill.assert_called_once_with(202, pilot.signal.SIGTERM)
            assert wait.call_args_list == [((False,), {}), ((True,), {})]
            assert json.loads(pidfile.read_text())["pid"] == 303

            # An unrelated listener is never stopped, even with a stale PID file.
            kill.reset_mock()
            start.reset_mock()
            with patch.object(pilot, "listener", return_value=404):
                try:
                    pilot.main()
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
                    pilot.main()
                except RuntimeError:
                    pass
                else:
                    raise AssertionError("Unrecognized command was accepted")
            kill.assert_not_called()
            start.assert_not_called()
    print("Fictional pilot startup, restart and unrecognized-listener checks passed")


if __name__ == "__main__":
    main()
