"""Run a real-server API-key check using only fresh, isolated fictional data.

The pinned images must already exist locally. A new project-private fixture
directory and stopped containers are retained; no browser or live POC is used.
"""

import json
import os
import re
import secrets
import shutil
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
POC = ROOT / "docs/research/tracker-poc"
PRIVATE = ROOT / ".cache/tracker-poc/private"
IMAGES = {
    "postgres": "postgres:16-alpine@sha256:0cefaabd882e42bcb2a2f3dc56d3ce4770560ba62fd7f197f1a2e008fd5731ab",
    "kaneo": "ghcr.io/usekaneo/kaneo:2.49.0@sha256:cd1826b1aba3ce736015cadf6f6c975d923aac00f4b6aaa7aedb29bc722dae49",
    "client": "python@sha256:f3fa41d74a768c2fce8016b98c191ae8c1bacd8f1152870a3f9f87d350920b7c",
}


def command(args, *, timeout=120):
    try:
        result = subprocess.run(args, capture_output=True, check=False, timeout=timeout)
    except (OSError, subprocess.SubprocessError):
        raise RuntimeError("Fictional fixture command could not complete") from None
    if result.returncode:
        # Child output can contain fictional credentials; do not surface it.
        safe = re.search(
            rb"Fictional bearer check failed at (?:readiness|signup|workspace|project|fields|task|key|owner|watched|preview|apply|retry|clear|lifecycle|denial): [A-Za-z]+(?: HTTP [0-9]{3})?",
            result.stderr,
        )
        if safe:
            raise RuntimeError(safe.group().decode())
        raise RuntimeError("Fictional fixture command failed")
    return result.stdout


def check_config(config, directory):
    services = config.get("services", {})
    if set(services) != set(IMAGES):
        raise ValueError("Unexpected fictional fixture services")
    networks = config.get("networks", {})
    if set(networks) != {"fictional"} or networks["fictional"].get("internal") is not True:
        raise ValueError("Fixture network must be internal")
    expected_mounts = {
        "postgres": {(str((directory / "postgres").resolve()), "/var/lib/postgresql/data", False)},
        "kaneo": set(),
        "client": {(str((directory / "source").resolve()), "/work", True)},
    }
    for name, service in services.items():
        mounts = set()
        for volume in service.get("volumes", []):
            if volume.get("type") != "bind":
                raise ValueError("Unexpected fixture volume")
            mounts.add(
                (
                    str(Path(volume["source"]).resolve()),
                    volume["target"],
                    bool(volume.get("read_only", False)),
                )
            )
        if (
            service.get("image") != IMAGES[name]
            or set(service.get("networks", {})) != {"fictional"}
            or service.get("ports")
            or service.get("logging", {}).get("driver") != "none"
            or mounts != expected_mounts[name]
        ):
            raise ValueError("Fixture image, network, ports or mounts are unexpected")


def main():
    if (
        not PRIVATE.is_dir()
        or PRIVATE.stat().st_uid != os.getuid()
        or PRIVATE.stat().st_mode & 0o077
    ):
        raise ValueError("Owner-only project-private directory is unavailable")
    suffix = secrets.token_hex(6)
    directory = PRIVATE / f"kaneo-bearer-fixture-{suffix}"
    directory.mkdir(mode=0o700)
    (directory / "postgres").mkdir(mode=0o700)
    (directory / "source").mkdir(mode=0o700)
    shutil.copyfile(POC / "kaneo-bearer-fixture/compose.yaml", directory / "compose.yaml")
    for name in (
        "direct_review_links.py",
        "direct_review_links_check.py",
        "enrichment.py",
        "kaneo_direct_reviews.py",
        "kaneo_enrich.py",
        "kaneo_movary_mapping.py",
        "kaneo_smoke.py",
    ):
        shutil.copyfile(POC / name, directory / "source" / name)
    watched_source = directory / "source/docs/research/tracker-poc"
    watched_source.mkdir(mode=0o700, parents=True)
    shutil.copyfile(POC / "kaneo_watched_refresh.py", watched_source / "kaneo_watched_refresh.py")
    (directory / "source/film_iq").mkdir(mode=0o700)
    for name in ("__init__.py", "personal_identity.py", "personal_io.py"):
        shutil.copyfile(ROOT / "src/film_iq" / name, directory / "source/film_iq" / name)
    (directory / "source/film_iq/availability").mkdir(mode=0o700)
    for name in ("__init__.py", "tmdb.py"):
        shutil.copyfile(
            ROOT / "src/film_iq/availability" / name,
            directory / "source/film_iq/availability" / name,
        )
    shutil.copyfile(POC / "kaneo-bearer-fixture/client.py", directory / "source/client.py")
    env = {
        "POSTGRES_DB": "kaneo",
        "POSTGRES_USER": "kaneo",
        "POSTGRES_PASSWORD": secrets.token_hex(24),
        "AUTH_SECRET": secrets.token_hex(32),
        "FIXTURE_PASSWORD": secrets.token_urlsafe(24),
        "KANEO_CLIENT_URL": "http://kaneo:5173",
        "CORS_ORIGINS": "http://kaneo:5173",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONPATH": "/work/docs/research/tracker-poc",
    }
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    fd = os.open(directory / "fixture.env", flags, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as file:
        file.write("".join(f"{key}={value}\n" for key, value in env.items()))
    compose = [
        "docker",
        "compose",
        "-p",
        f"filmiq-bearer-{suffix}",
        "-f",
        str(directory / "compose.yaml"),
    ]
    check_config(json.loads(command([*compose, "config", "--format", "json"])), directory)
    started = False
    try:
        started = True
        command([*compose, "up", "-d", "--no-deps", "--pull", "never", "postgres"])
        for attempt in range(60):
            ready = subprocess.run(
                [*compose, "exec", "-T", "postgres", "pg_isready", "-U", "kaneo", "-d", "kaneo"],
                capture_output=True,
                check=False,
                timeout=5,
            )
            if ready.returncode == 0:
                break
            if attempt == 59:
                raise RuntimeError("Fictional database did not become ready")
            time.sleep(1)
        command([*compose, "up", "-d", "--no-deps", "--pull", "never", "kaneo", "client"])
        output = command(
            [*compose, "exec", "-T", "client", "python", "/work/client.py"], timeout=120
        )
        if (
            output.strip()
            != b"Fictional real-server key, import, lifecycle, metadata and denial checks passed"
        ):
            raise RuntimeError("Unexpected fictional fixture result")
        print(output.decode().strip())
    finally:
        if started:
            command([*compose, "stop"], timeout=90)
    print("Fictional fixture stopped; project-local data retained")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        message = (
            str(error) if isinstance(error, (RuntimeError, ValueError)) else type(error).__name__
        )
        print(f"Fictional bearer fixture stopped: {message}")
        raise SystemExit(1) from None
