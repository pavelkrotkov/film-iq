"""Start or restart the scoped Kaneo pilot with a private maintenance log."""

import argparse
import json
import os
import signal
import socket
import stat
import subprocess
import time
from collections.abc import Mapping
from pathlib import Path

from tmdb_live import approval

ROOT = Path(__file__).resolve().parents[3]
PRIVATE = ROOT / ".cache/tracker-poc/private"
PID_FILE = PRIVATE / "kaneo-live-pilot-pid.json"
LOG_FILE = PRIVATE / "kaneo-live-pilot.log"
BRIDGE = "docs/research/tracker-poc/tmdb_live.py"


def listener() -> int | None:
    result = subprocess.run(
        ["lsof", "-t", "-nP", "-iTCP:15176", "-sTCP:LISTEN"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode not in (0, 1) or (result.returncode == 1 and result.stderr.strip()):
        raise RuntimeError("Could not inspect the bridge listener")
    pids = result.stdout.split()
    if len(pids) > 1:
        raise RuntimeError("Multiple bridge listeners")
    return int(pids[0]) if pids else None


def wait_for_listener(expected: bool) -> None:
    for _ in range(100):
        with socket.socket() as sock:
            sock.settimeout(0.2)
            listening = sock.connect_ex(("127.0.0.1", 15176)) == 0
        if listening == expected:
            return
        time.sleep(0.1)
    raise RuntimeError("Bridge listener did not reach the expected state")


def intended_configuration(env: Mapping[str, str], pid_file: Path, override: str | None = None):
    try:
        saved = json.loads(pid_file.read_text())
    except FileNotFoundError:
        saved = {}
    except (OSError, ValueError, TypeError):
        raise ValueError("Pilot configuration metadata is unavailable") from None
    if not isinstance(saved, dict):
        raise ValueError("Invalid pilot configuration metadata")
    scope = override or saved.get("scope", "pilot")
    pace = env.get("FILMIQ_TMDB_PACE", saved.get("tmdb_pace", "0"))
    refresh = env.get("FILMIQ_TMDB_REFRESH_ENABLED", saved.get("tmdb_refresh_enabled", "1"))
    if scope not in ("pilot", "collection") or pace not in ("0", "1") or refresh not in ("0", "1"):
        raise ValueError("Invalid pilot scope or TMDB settings")
    if scope == "collection" and pace != "1":
        raise ValueError("Collection mode requires paced TMDB requests")
    return scope, pace, refresh


def environment(scope: str, pace: str, refresh: str) -> dict[str, str]:
    if scope not in ("pilot", "collection") or pace not in ("0", "1") or refresh not in ("0", "1"):
        raise ValueError("Invalid pilot scope or TMDB settings")
    if scope == "collection" and pace != "1":
        raise ValueError("Collection mode requires paced TMDB requests")
    names = {"TMDB_API_KEY", "TMDB_READ_ACCESS_TOKEN"}
    env = os.environ.copy()
    for name in names | {
        "FILMIQ_APPROVAL_DIR",
        "FILMIQ_CATALOG_APPROVAL_DIR",
        "FILMIQ_TMDB_CACHE_ENABLE",
        "FILMIQ_TMDB_CACHE_DIRECTORY",
        "FILMIQ_REVIEWED_CATALOG",
        "FILMIQ_TMDB_PACE",
        "FILMIQ_TMDB_REFRESH_ENABLED",
    }:
        env.pop(name, None)
    credentials = {}
    for line in (PRIVATE / "youtrack-tmdb-live.env").read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        name, separator, value = line.partition("=")
        if name not in names:
            continue
        if (
            not separator
            or name in credentials
            or not value
            or not value.isascii()
            or any(char.isspace() for char in value)
            or value.startswith(('"', "'"))
        ):
            raise ValueError("Invalid credential configuration")
        credentials[name] = value
    if not credentials:
        raise ValueError("Credential unavailable")
    pilot_dir = PRIVATE / "tmdb-pilot-approval"
    catalog_dir = PRIVATE / "tmdb-approval"
    pilot = approval.parse_allowlist(
        approval.decode_allowlist((pilot_dir / "approved-ids.json").read_text())
    )
    catalog_bytes = (catalog_dir / "approved-ids.json").read_bytes()
    catalog = approval.parse_allowlist(approval.decode_allowlist(catalog_bytes.decode("utf-8")))
    selected = json.loads((pilot_dir / "selection.json").read_text())["tmdb_id"]
    if type(selected) is not int or pilot != {selected} or not pilot.issubset(catalog):
        raise ValueError("Pilot approval does not match the selected film")
    if scope == "collection":
        approval.validate_collection_approval(
            catalog_bytes,
            (PRIVATE / "film-input.json").read_bytes(),
            (PRIVATE / "tmdb-watched-lookup-preview.md").read_bytes(),
        )
    provider_dir = catalog_dir if scope == "collection" else pilot_dir
    reviewed = (
        ROOT.parent.parent / ".cache/epic-c/results/reviewed-display-catalog-expanded-20261031.json"
    )
    cache = PRIVATE / "tmdb-live-cache/kaneo"
    if not reviewed.is_file() or not all(
        (cache / name).exists() for name in ("policy.json", "authority.json", "cache")
    ):
        raise ValueError("Pilot cache or reviewed catalog unavailable")
    env.update(credentials)
    env.update(
        FILMIQ_APPROVAL_DIR=str(provider_dir),
        FILMIQ_CATALOG_APPROVAL_DIR=str(catalog_dir),
        FILMIQ_TMDB_CACHE_ENABLE="1",
        FILMIQ_TMDB_CACHE_DIRECTORY=str(cache),
        FILMIQ_REVIEWED_CATALOG=str(reviewed),
        FILMIQ_TMDB_PACE=pace,
        FILMIQ_TMDB_REFRESH_ENABLED=refresh,
        PYTHONDONTWRITEBYTECODE="1",
    )
    return env


def verified_listener() -> int | None:
    """Identify the recorded bridge, refusing any other listener."""
    pid = listener()
    if pid is None:
        return None
    try:
        recorded = json.loads(PID_FILE.read_text())["pid"]
    except (OSError, ValueError, KeyError, TypeError):
        raise RuntimeError("The bridge listener is not the recorded pilot") from None
    if pid != recorded:
        raise RuntimeError("The bridge listener is not the recorded pilot")
    command = subprocess.check_output(["ps", "-p", str(pid), "-o", "command="], text=True).strip()
    if not command.endswith(BRIDGE):
        raise RuntimeError("The bridge listener is not the recorded pilot")
    return pid


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--collection", action="store_const", const="collection", dest="scope")
    group.add_argument("--pilot", action="store_const", const="pilot", dest="scope")
    group.add_argument("--stop", action="store_true", help="stop only the recorded bridge")
    group.add_argument("--start-only", action="store_true", help="leave a running bridge untouched")
    args = parser.parse_args(argv)
    if args.stop:
        pid = verified_listener()
        if pid is not None:
            os.kill(pid, signal.SIGTERM)
            wait_for_listener(False)
        print(
            "Kaneo pilot bridge stopped"
            if pid is not None
            else "Kaneo pilot bridge already stopped"
        )
        return
    pid = verified_listener()
    if args.start_only and pid is not None:
        print("Kaneo pilot bridge already running; left unchanged")
        return
    scope, pace, refresh = intended_configuration(os.environ, PID_FILE, args.scope)
    env = environment(scope, pace, refresh)
    flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND | os.O_NOFOLLOW
    fd = os.open(LOG_FILE, flags, 0o600)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
            raise PermissionError("Pilot log must be an owner-only regular file")
        if pid is not None:
            os.kill(pid, signal.SIGTERM)
            wait_for_listener(False)
        process = subprocess.Popen(
            [str(ROOT / ".venv/bin/python"), BRIDGE],
            cwd=ROOT,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=fd,
            stderr=fd,
            start_new_session=True,
        )
        try:
            wait_for_listener(True)
            if process.poll() is not None or listener() != process.pid:
                raise RuntimeError("Pilot bridge did not start")
        except Exception:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=10)
            raise
        PID_FILE.write_text(
            json.dumps(
                {
                    "pid": process.pid,
                    "cache_enabled": True,
                    "scope": scope,
                    "tmdb_pace": pace,
                    "tmdb_refresh_enabled": refresh,
                }
            )
        )
        PID_FILE.chmod(0o600)
    finally:
        os.close(fd)
    print("Kaneo pilot bridge started with owner-only logging")


if __name__ == "__main__":
    main()
