"""Fictional startup ordering and fail-closed checks; no services are touched."""

import json
import sqlite3
import tempfile
import urllib.error
from email.message import Message
from pathlib import Path
from unittest.mock import MagicMock, patch

import start_local_pocs as startup


class Fake:
    python = Path("/fictional/python")
    ui = Path("/fictional/ui")

    def __init__(self, *, running=(), occupied=(), fail_ready=None, missing=False):
        self.running = set(running)
        self.ports = set(occupied)
        self.fail_ready = fail_ready
        self.missing = missing
        self.calls = []

    def preflight(self):
        self.calls.append("preflight")
        if self.missing:
            raise startup.StartupError("Existing preference database is missing")

    def container_state(self, name):
        self.calls.append(("state", name))
        return "running" if name in self.running else "exited"

    def container_start(self, name):
        self.calls.append(("start", name))
        self.running.add(name)

    def postgres_ready(self):
        return True

    def bridge_ready(self):
        return startup.CONTAINERS["bridge"] in self.running

    def http_ready(self, url):
        return True

    def wait(self, check, label):
        self.calls.append(("wait", label))
        if label == self.fail_ready or not check():
            raise startup.StartupError("Fictional readiness timeout")

    def occupied(self, port):
        return port in self.ports

    def launch(self, name, args, cwd, port):
        self.calls.append(("launch", name, port))
        assert port not in self.ports
        self.ports.add(port)

    def start_pilot(self):
        self.calls.append("start-only pilot")
        assert 15176 not in self.ports


def main():
    f = Fake()
    messages, incomplete = startup.start(f)
    assert not incomplete and messages[-1].endswith("started with recorded settings")
    starts = [call[1] for call in f.calls if isinstance(call, tuple) and call[0] == "start"]
    assert starts == [
        startup.CONTAINERS[name] for name in ("postgres", "kaneo", "youtrack", "bridge")
    ]
    assert f.calls.index(("wait", "PostgreSQL")) < f.calls.index(
        ("start", startup.CONTAINERS["kaneo"])
    )
    assert f.calls.index(("wait", "YouTrack")) < f.calls.index(
        ("start", startup.CONTAINERS["bridge"])
    )
    assert ("launch", "ui", 15174) in f.calls and ("launch", "preferences", 15175) in f.calls
    assert "start-only pilot" in f.calls

    existing = Fake(running=startup.CONTAINERS.values(), occupied=(15174, 15175, 15176))
    messages, incomplete = startup.start(existing)
    assert (
        incomplete
        and sum("left untouched and not verified" in message for message in messages) == 3
    )
    assert not any(
        isinstance(call, tuple) and call[0] in ("start", "launch") for call in existing.calls
    )
    assert "start-only pilot" not in existing.calls

    for options in ({"missing": True}, {"fail_ready": "PostgreSQL"}):
        failed = Fake(**options)
        try:
            startup.start(failed)
        except startup.StartupError:
            pass
        else:
            raise AssertionError("Incomplete preflight or readiness must stop startup")
        assert ("start", startup.CONTAINERS["kaneo"]) not in failed.calls
        assert "start-only pilot" not in failed.calls

    class CrashedBridge(Fake):
        def container_start(self, name):
            super().container_start(name)
            if name == startup.CONTAINERS["bridge"]:
                self.running.remove(name)

    crashed = CrashedBridge()
    try:
        startup.start(crashed)
    except startup.StartupError:
        pass
    else:
        raise AssertionError("An unresponsive metadata bridge must stop startup")
    assert ("wait", "YouTrack metadata bridge") in crashed.calls
    assert not any(isinstance(call, tuple) and call[0] == "launch" for call in crashed.calls)

    # The real probe executes only an unauthenticated loopback request inside the bridge.
    probe = startup.Local()
    with patch.object(startup.subprocess, "run", return_value=MagicMock(returncode=0)) as run:
        assert probe.bridge_ready()
        args = run.call_args.args[0]
        assert args[:5] == ["docker", "exec", startup.CONTAINERS["bridge"], "python", "-c"]
        assert "127.0.0.1" in args[5] and "15178" in args[5] and "401" in args[5]
    with patch.object(startup.subprocess, "run", return_value=MagicMock(returncode=1)):
        assert not probe.bridge_ready()

    # Exercise the real preflight with a synthetic project and absent database.
    with tempfile.TemporaryDirectory(dir=startup.ROOT / ".cache/tracker-poc") as folder:
        root = Path(folder)
        private = root / ".cache/tracker-poc/private"
        private.mkdir(mode=0o700, parents=True)
        (private / "kaneo-live-pilot-pid.json").write_text(
            json.dumps(
                {
                    "cache_enabled": True,
                    "scope": "collection",
                    "tmdb_pace": "1",
                    "tmdb_refresh_enabled": "0",
                }
            )
        )
        (private / "youtrack-tmdb-live.env").write_text("fictional")
        python = root / ".venv/bin/python"
        python.parent.mkdir(parents=True)
        python.write_text("fictional")
        python.chmod(0o700)
        bundle = root / "docs/research/tracker-poc/ui/dist/app.js"
        bundle.parent.mkdir(parents=True)
        bundle.write_text("fictional")
        with patch.object(startup, "ROOT", root), patch.object(startup, "PRIVATE", private):
            local = startup.Local()
            with patch.object(
                local, "container_state", side_effect=AssertionError("Docker called")
            ):
                try:
                    local.preflight()
                except startup.StartupError as error:
                    assert "database" in str(error)
                else:
                    raise AssertionError("Missing real preference DB check was bypassed")
            database = root / ".cache/tracker-poc/preferences.sqlite3"
            with sqlite3.connect(database) as connection:
                connection.execute("CREATE TABLE unrelated (value TEXT)")
            with patch.object(
                local, "container_state", side_effect=AssertionError("Docker called")
            ):
                try:
                    local.preflight()
                except startup.StartupError as error:
                    assert "database schema" in str(error)
                else:
                    raise AssertionError("Empty preference database schema was accepted")
            with sqlite3.connect(database) as connection:
                connection.execute(
                    "CREATE TABLE preferences (user_id TEXT, task_id TEXT, interest_score INTEGER, watchlist INTEGER, watched_at TEXT, personal_notes TEXT)"
                )
            with patch.object(
                local, "container_state", side_effect=AssertionError("Docker called")
            ):
                try:
                    local.preflight()
                except startup.StartupError as error:
                    assert "database schema" in str(error)
                else:
                    raise AssertionError("Preference table without its primary key was accepted")
            with sqlite3.connect(database) as connection:
                connection.execute("DROP TABLE preferences")
                connection.execute(
                    "CREATE TABLE preferences (user_id TEXT, task_id TEXT, interest_score INTEGER, watchlist INTEGER, watched_at TEXT, personal_notes TEXT, PRIMARY KEY(user_id, task_id))"
                )
            with (
                patch.object(local, "container_state", side_effect=AssertionError("Docker called")),
                patch.object(
                    startup.kaneo_live_pilot, "environment", side_effect=FileNotFoundError
                ),
            ):
                try:
                    local.preflight()
                except startup.StartupError as error:
                    assert "approval, cache or configuration" in str(error)
                else:
                    raise AssertionError("Missing pilot inputs were not rejected before startup")

    # A local redirect must be reported as reachability without following it.
    redirect = urllib.error.HTTPError("http://127.0.0.1:18180/", 302, "redirect", Message(), None)
    opener = MagicMock()
    opener.open.side_effect = redirect
    with patch.object(startup.urllib.request, "build_opener", return_value=opener) as factory:
        assert startup.Local().http_ready("http://127.0.0.1:18180/")
        assert any(isinstance(item, startup.NoRedirect) for item in factory.call_args.args)
        opener.open.assert_called_once()
    print("Fictional startup ordering, missing database and occupied-listener checks passed")


if __name__ == "__main__":
    main()
