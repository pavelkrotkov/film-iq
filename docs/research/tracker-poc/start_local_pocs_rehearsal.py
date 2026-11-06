"""Rehearse the startup orchestrator with fictional loopback processes.

Docker and the pilot executable are fictional. No tracker, provider, credential,
or browser session is accessed. Temporary project data stays in this worktree.
"""

import json
import os
import signal
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
import urllib.request
from contextlib import suppress
from pathlib import Path
from unittest.mock import patch

import start_local_pocs as startup


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def executable(path, source):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source)
    path.chmod(0o700)


def main():
    private_root = startup.PRIVATE
    ports = {name: free_port() for name in ("kaneo", "youtrack", "ui", "preferences", "pilot")}
    assert len(set(ports.values())) == len(ports)
    children = []
    original_popen = subprocess.Popen

    # Capture only subprocesses launched by this test, including fictional docker.
    def capture(*args, **kwargs):
        process = original_popen(*args, **kwargs)
        children.append(process)
        return process

    with tempfile.TemporaryDirectory(dir=private_root, prefix="fictional-startup-") as directory:
        root = Path(directory)
        private = root / ".cache/tracker-poc/private"
        private.mkdir(mode=0o700, parents=True)
        ui = root / "docs/research/tracker-poc/ui"
        (ui / "dist").mkdir(parents=True)
        (ui / "dist/app.js").write_text("fictional bundle")
        db = root / ".cache/tracker-poc/preferences.sqlite3"
        with sqlite3.connect(db) as conn:
            conn.execute(
                "CREATE TABLE preferences (user_id TEXT, task_id TEXT, interest_score INTEGER, "
                "watchlist INTEGER, watched_at TEXT, personal_notes TEXT, PRIMARY KEY(user_id, task_id))"
            )
        (private / "youtrack-tmdb-live.env").write_text("fictional")
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
        state = private / "fake-docker.json"
        state.write_text(json.dumps({name: "exited" for name in startup.CONTAINERS.values()}))
        docker = private / "bin/docker"
        executable(
            docker,
            "#!/usr/bin/env python3\n"
            "import json, os, pathlib, sys\n"
            "p=pathlib.Path(os.environ['FAKE_DOCKER_STATE']); s=json.loads(p.read_text())\n"
            "a=sys.argv[1:]\n"
            "if a[0]=='inspect': print(s[a[-1]])\n"
            "elif a[0]=='start': s[a[1]]='running'; p.write_text(json.dumps(s))\n"
            "elif a[0]=='exec': sys.exit(0 if s[a[1]]=='running' else 1)\n"
            "else: sys.exit(1)\n",
        )
        # The fake pilot executes via the real Local.start_pilot subprocess path.
        pilot = root / "docs/research/tracker-poc/kaneo_live_pilot.py"
        executable(
            pilot,
            "import os, pathlib, subprocess, sys\n"
            "assert sys.argv[1:]==['--start-only']\n"
            "assert 'FILMIQ_TMDB_PACE' not in os.environ\n"
            "assert 'FILMIQ_TMDB_REFRESH_ENABLED' not in os.environ\n"
            "p=subprocess.Popen([sys.executable,'-m','http.server',os.environ['FAKE_PILOT_PORT'],'--bind','127.0.0.1'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)\n"
            "pathlib.Path(os.environ['FAKE_PILOT_PID']).write_text(str(p.pid))\n",
        )

        class Fictional(startup.Local):
            def __init__(self):
                super().__init__()
                self.python = Path(sys.executable)
                self.ui = ui

            def http_ready(self, url):
                # Fake docker tracks the two fictional tracker states; no real endpoint is queried.
                name = "kaneo" if ":15173/" in url else "youtrack"
                return self.container_state(startup.CONTAINERS[name]) == "running"

            def occupied(self, port):
                return super().occupied(
                    ports[{15174: "ui", 15175: "preferences", 15176: "pilot"}[port]]
                )

            def launch(self, name, args, cwd, port):
                actual = ports[name]
                super().launch(
                    name,
                    [str(self.python), "-m", "http.server", str(actual), "--bind", "127.0.0.1"],
                    root,
                    actual,
                )

        env = {
            "PATH": f"{docker.parent}:{os.environ.get('PATH', '')}",
            "FAKE_DOCKER_STATE": str(state),
            "FAKE_PILOT_PORT": str(ports["pilot"]),
            "FAKE_PILOT_PID": str(private / "fake-pilot.pid"),
            # Verify the real pilot wrapper removes inherited overrides.
            "FILMIQ_TMDB_PACE": "0",
            "FILMIQ_TMDB_REFRESH_ENABLED": "1",
        }
        try:
            with (
                patch.dict(os.environ, env),
                patch.object(startup, "ROOT", root),
                patch.object(startup, "PRIVATE", private),
                patch.object(startup.kaneo_live_pilot, "environment", return_value={}),
                patch.object(subprocess, "Popen", side_effect=capture),
            ):
                runtime = Fictional()
                messages, occupied = startup.start(runtime)
                assert not occupied
                assert [m.split(":")[0] for m in messages[:4]] == [
                    "postgres",
                    "kaneo",
                    "youtrack",
                    "bridge",
                ]
                assert all(value == "running" for value in json.loads(state.read_text()).values())
                for name in ("ui", "preferences", "pilot"):
                    for _ in range(30):
                        try:
                            with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(
                                f"http://127.0.0.1:{ports[name]}/", timeout=1
                            ) as response:
                                assert response.status == 200
                                break
                        except OSError:
                            time.sleep(0.1)
                    else:
                        raise AssertionError(f"Fictional {name} did not become ready")
                before = [runtime.listeners(ports[name]) for name in ("ui", "preferences", "pilot")]
                _, occupied = startup.start(runtime)
                after = [runtime.listeners(ports[name]) for name in ("ui", "preferences", "pilot")]
                assert occupied and before == after and all(len(pids) == 1 for pids in before)
                # Stop only our fictional preference process and recover it.
                pref_pid = next(iter(before[1]))
                pref = next(child for child in children if child.pid == pref_pid)
                pref.terminate()
                pref.wait(timeout=5)
                assert not runtime.listeners(ports["preferences"])
                recovered, occupied = startup.start(runtime)
                final = [runtime.listeners(ports[name]) for name in ("ui", "preferences", "pilot")]
                assert occupied and "preferences: started" in recovered
                assert final[0] == before[0] and final[2] == before[2]
                assert len(final[1]) == 1 and final[1] != before[1]
        finally:
            # The pilot server is a child of the fictional launcher, not this process.
            pid_file = private / "fake-pilot.pid"
            if pid_file.exists():
                with suppress(ProcessLookupError):
                    os.kill(int(pid_file.read_text()), signal.SIGTERM)
            for child in children:
                if child.poll() is None:
                    child.terminate()
                    child.wait(timeout=5)
    print("Fictional cold startup, repeat and isolated process recovery passed")


if __name__ == "__main__":
    main()
