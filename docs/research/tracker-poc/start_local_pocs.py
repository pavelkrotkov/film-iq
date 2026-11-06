"""Start the existing local tracker POCs once, without stopping other services.

Run from the configured worktree with its virtualenv. This is not a setup,
recovery, provider refresh, or automatic-login service.
"""

import json
import os
import sqlite3
import stat
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import kaneo_live_pilot

ROOT = Path(__file__).resolve().parents[3]
PRIVATE = ROOT / ".cache/tracker-poc/private"
CONTAINERS = {
    "postgres": "film-iq-tracker-poc-postgres-1",
    "kaneo": "film-iq-tracker-poc-kaneo-1",
    "youtrack": "film-iq-tracker-poc-youtrack-1",
    "bridge": "film-iq-tracker-poc-tmdb-live-bridge-1",
}


class StartupError(RuntimeError):
    """A startup step failed without exposing private output."""


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class Local:
    def __init__(self):
        self.python = ROOT / ".venv/bin/python"
        self.ui = ROOT / "docs/research/tracker-poc/ui"

    def command(self, args):
        try:
            result = subprocess.run(args, capture_output=True, text=True, timeout=20, check=False)
        except (OSError, subprocess.SubprocessError):
            raise StartupError("A local command could not run") from None
        if result.returncode:
            raise StartupError("A local command failed")
        return result.stdout.strip()

    def preflight(self):
        required = (
            self.python,
            self.ui / "dist/app.js",
            ROOT / ".cache/tracker-poc/preferences.sqlite3",
            PRIVATE / "kaneo-live-pilot-pid.json",
            PRIVATE / "youtrack-tmdb-live.env",
        )
        if (
            not PRIVATE.is_dir()
            or PRIVATE.stat().st_uid != os.getuid()
            or PRIVATE.stat().st_mode & 0o077
        ):
            raise StartupError("The owner-only private directory is unavailable")
        if not all(path.is_file() for path in required) or not os.access(self.python, os.X_OK):
            raise StartupError(
                "Existing UI, preference database, pilot configuration or interpreter is missing"
            )
        database = ROOT / ".cache/tracker-poc/preferences.sqlite3"
        try:
            # Immutable mode avoids creating SQLite journal/shared-memory files.
            with sqlite3.connect(database.as_uri() + "?mode=ro&immutable=1", uri=True) as conn:
                columns = {row[1]: row[5] for row in conn.execute("PRAGMA table_info(preferences)")}
        except sqlite3.Error:
            raise StartupError("Existing preference database is invalid") from None
        if columns != {
            "user_id": 1,
            "task_id": 2,
            "interest_score": 0,
            "watchlist": 0,
            "watched_at": 0,
            "personal_notes": 0,
        }:
            raise StartupError("Existing preference database schema is unavailable")
        try:
            pilot = json.loads((PRIVATE / "kaneo-live-pilot-pid.json").read_text())
        except (OSError, ValueError, TypeError):
            raise StartupError("Recorded Kaneo pilot configuration is unavailable") from None
        if not isinstance(pilot, dict) or (
            pilot.get("cache_enabled") is not True
            or pilot.get("scope") != "collection"
            or pilot.get("tmdb_pace") != "1"
            or pilot.get("tmdb_refresh_enabled") not in ("0", "1")
        ):
            raise StartupError(
                "Recorded Kaneo pilot configuration is not the existing collection setup"
            )
        try:
            # Use the launcher's non-network checks before starting any service.
            kaneo_live_pilot.environment(
                "collection", pilot["tmdb_pace"], pilot["tmdb_refresh_enabled"]
            )
        except (OSError, ValueError, KeyError, TypeError):
            raise StartupError(
                "Kaneo pilot approval, cache or configuration is unavailable"
            ) from None
        for name in CONTAINERS.values():
            self.container_state(name)

    def container_state(self, name):
        value = self.command(["docker", "inspect", "--format", "{{.State.Status}}", name])
        if value not in ("running", "exited", "created"):
            raise StartupError("An existing container is unavailable or in an unsupported state")
        return value

    def container_start(self, name):
        self.command(["docker", "start", name])

    def postgres_ready(self):
        try:
            result = subprocess.run(
                [
                    "docker",
                    "exec",
                    CONTAINERS["postgres"],
                    "pg_isready",
                    "-U",
                    "kaneo",
                    "-d",
                    "kaneo",
                ],
                capture_output=True,
                timeout=5,
                check=False,
            )
            return result.returncode == 0
        except (OSError, subprocess.SubprocessError):
            return False

    def http_ready(self, url):
        # Loopback only; ignore configured HTTP proxies and never use sessions.
        if url not in ("http://127.0.0.1:15173/", "http://127.0.0.1:18180/"):
            raise StartupError("Unexpected readiness URL")
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
        try:
            with opener.open(url, timeout=2) as response:
                return 200 <= response.status < 500
        except urllib.error.HTTPError as error:
            return 300 <= error.code < 500
        except (OSError, urllib.error.URLError, TimeoutError):
            return False

    def wait(self, check, label, attempts=30):
        for _ in range(attempts):
            if check():
                return
            time.sleep(1)
        raise StartupError(f"{label} did not become reachable in time")

    def listeners(self, port):
        try:
            result = subprocess.run(
                ["lsof", "-t", "-nP", f"-iTCP:{port}", "-sTCP:LISTEN"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
        except (OSError, subprocess.SubprocessError):
            raise StartupError("Could not inspect a local listener") from None
        if result.returncode not in (0, 1) or (result.returncode == 1 and result.stderr.strip()):
            raise StartupError("Could not inspect a local listener")
        try:
            return {int(pid) for pid in result.stdout.split()}
        except ValueError:
            raise StartupError("Could not interpret a local listener") from None

    def occupied(self, port):
        return bool(self.listeners(port))

    def launch(self, name, args, cwd, port):
        log = PRIVATE / f"startup-{name}.log"
        flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND | os.O_NOFOLLOW
        fd = os.open(log, flags, 0o600)
        try:
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
                raise StartupError("Startup log must be an owner-only regular file")
            child = subprocess.Popen(
                args,
                cwd=cwd,
                stdin=subprocess.DEVNULL,
                stdout=fd,
                stderr=fd,
                start_new_session=True,
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            )
        finally:
            os.close(fd)
        for _ in range(30):
            if child.poll() is not None:
                raise StartupError(f"{name} exited during startup; inspect its private log")
            listeners = self.listeners(port)
            if listeners == {child.pid}:
                return
            if listeners:
                raise StartupError(f"{name} port was taken by another listener; left untouched")
            time.sleep(0.2)
        raise StartupError(f"{name} startup was not confirmed; inspect its private log")

    def start_pilot(self):
        env = os.environ.copy()
        for name in ("FILMIQ_TMDB_PACE", "FILMIQ_TMDB_REFRESH_ENABLED"):
            env.pop(name, None)
        try:
            result = subprocess.run(
                [str(self.python), "docs/research/tracker-poc/kaneo_live_pilot.py", "--start-only"],
                cwd=ROOT,
                env=env,
                capture_output=True,
                timeout=30,
                check=False,
            )
        except (OSError, subprocess.SubprocessError):
            raise StartupError("Kaneo metadata bridge startup could not be confirmed") from None
        if result.returncode:
            raise StartupError("Kaneo metadata bridge startup failed; inspect its private log")


def start(runtime, report=lambda message: None):
    """Start only absent processes; an occupied local port is never touched."""
    runtime.preflight()
    messages = []

    def record(message):
        messages.append(message)
        report(message)

    for name in ("postgres", "kaneo", "youtrack", "bridge"):
        container = CONTAINERS[name]
        if runtime.container_state(container) != "running":
            runtime.container_start(container)
            record(f"{name}: started")
        else:
            record(f"{name}: already running")
        if name == "postgres":
            runtime.wait(runtime.postgres_ready, "PostgreSQL")
        elif name == "kaneo":
            runtime.wait(lambda: runtime.http_ready("http://127.0.0.1:15173/"), "Kaneo")
        elif name == "youtrack":
            runtime.wait(lambda: runtime.http_ready("http://127.0.0.1:18180/"), "YouTrack")
    occupied = False
    for name, port, args, cwd in (
        (
            "ui",
            15174,
            [str(runtime.python), "-m", "http.server", "15174", "--bind", "127.0.0.1"],
            runtime.ui,
        ),
        (
            "preferences",
            15175,
            [str(runtime.python), "docs/research/tracker-poc/preferences.py"],
            ROOT,
        ),
    ):
        if runtime.occupied(port):
            record(f"{name}: port occupied; listener left untouched and not verified")
            occupied = True
        else:
            runtime.launch(name, args, cwd, port)
            record(f"{name}: started")
    if runtime.occupied(15176):
        record("Kaneo metadata bridge: port occupied; listener left untouched and not verified")
        occupied = True
    else:
        runtime.start_pilot()
        record("Kaneo metadata bridge: started with recorded settings")
    return messages, occupied


def main():
    try:
        os.umask(0o077)
        _, occupied = start(Local(), lambda message: print(message, flush=True))
        print("No provider lookup was requested. Sign in through the existing local interfaces.")
        if occupied:
            print("One or more existing listeners were not verified; check them before use.")
        return 2 if occupied else 0
    except (StartupError, OSError, ValueError) as error:
        print(f"Startup stopped: {error}", file=sys.stderr)
        print(
            "Existing services were not stopped or replaced; inspect the runbook before retrying.",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
