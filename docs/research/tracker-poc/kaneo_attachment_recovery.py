"""Rehearse fictional Kaneo attachment recovery in isolated Docker networks.

Creates a fresh owner-only directory under the selected project and leaves all
fixture files and containers in place. It does not access the live POCs.
"""

import hashlib
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TEMPLATE = ROOT / "docs/research/tracker-poc/kaneo-attachment-fixture"
PRIVATE = ROOT / ".cache/tracker-poc/private"


def call(args, *, input_bytes=None, timeout=120):
    result = subprocess.run(
        args, input=input_bytes, capture_output=True, timeout=timeout, check=False
    )
    if result.returncode:
        message = result.stderr.decode(errors="replace")
        detail = re.search(r"Fictional phase [a-z-]+: (?:Error|AssertionError|TypeError)", message)
        phase = next((value for value in ("create", "missing", "verify") if value in args), "setup")
        raise RuntimeError(
            f"Fixture {phase} failed ({result.returncode})"
            + (f": {detail.group(0)}" if detail else "")
        )
    return result.stdout


def save(path, content):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as output:
        output.write(content)


def digest_tree(root):
    return {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def wait(compose, service, args, label):
    for _ in range(60):
        result = subprocess.run(
            [*compose, "exec", "-T", service, *args],
            capture_output=True,
            timeout=5,
            check=False,
        )
        if result.returncode == 0:
            return
        time.sleep(1)
    raise RuntimeError(f"Fictional {label} was not ready")


def check_config(config, directory):
    """Reject an unexpected bind mount, network, published port or service."""
    services = {
        "source-db": "source",
        "source-garage": "source",
        "source-app": "source",
        "restored-db": "restored",
        "empty-garage": "restored",
        "restored-garage": "restored",
        "restored-app": "restored",
    }
    if set(config.get("services", {})) != set(services):
        raise RuntimeError("Unexpected fixture services")
    if set(config.get("networks", {})) != {"source", "restored"} or not all(
        value.get("internal") is True for value in config["networks"].values()
    ):
        raise RuntimeError("Fixture networks must be internal")
    for name, network in services.items():
        service = config["services"][name]
        if set(service.get("networks", {})) != {network} or service.get("ports"):
            raise RuntimeError("Fixture service network or ports are unexpected")
        if service.get("logging", {}).get("driver") != "none":
            raise RuntimeError("Fixture Docker logging must be disabled")
        for volume in service.get("volumes", []):
            if volume.get("type") != "bind" or not Path(volume["source"]).resolve().is_relative_to(
                directory.resolve()
            ):
                raise RuntimeError("Fixture bind mount is outside its new directory")


def main():
    if (
        not PRIVATE.is_dir()
        or PRIVATE.stat().st_uid != os.getuid()
        or PRIVATE.stat().st_mode & 0o077
    ):
        raise RuntimeError("Project-local private directory is unavailable")
    suffix = secrets.token_hex(6)
    directory = PRIVATE / f"kaneo-attachment-rehearsal-{suffix}"
    directory.mkdir(mode=0o700)
    for name in ("source-db", "restored-db", "source-garage", "empty-garage", "backup"):
        (directory / name).mkdir(mode=0o700)
    shutil.copyfile(TEMPLATE / "compose.yaml", directory / "compose.yaml")
    secret = secrets.token_hex(32)
    fixture_env = {
        "POSTGRES_DB": "kaneo",
        "POSTGRES_USER": "kaneo",
        "POSTGRES_PASSWORD": secrets.token_hex(24),
        "AUTH_SECRET": secrets.token_hex(32),
        "FIXTURE_PASSWORD": secrets.token_urlsafe(24),
        "KANEO_CLIENT_URL": "http://localhost:25173",
        "CORS_ORIGINS": "http://localhost:25173",
        "S3_ENDPOINT": "http://garage:3900",
        "S3_REGION": "garage",
        "S3_BUCKET": "fictional-attachments",
        "S3_ACCESS_KEY_ID": "GK" + secrets.token_hex(16),
        "S3_SECRET_ACCESS_KEY": secrets.token_hex(32),
        "GARAGE_DEFAULT_BUCKET": "fictional-attachments",
    }
    fixture_env["GARAGE_DEFAULT_ACCESS_KEY"] = fixture_env["S3_ACCESS_KEY_ID"]
    fixture_env["GARAGE_DEFAULT_SECRET_KEY"] = fixture_env["S3_SECRET_ACCESS_KEY"]
    save(
        directory / "fixture.env",
        "".join(f"{key}={value}\n" for key, value in fixture_env.items()).encode(),
    )
    save(
        directory / "garage.toml",
        (
            'metadata_dir = "/var/lib/garage/meta"\n'
            'data_dir = "/var/lib/garage/data"\n'
            'db_engine = "sqlite"\nreplication_factor = 1\n'
            'rpc_bind_addr = "[::]:3901"\nrpc_public_addr = "127.0.0.1:3901"\n'
            f'rpc_secret = "{secret}"\n'
            '[s3_api]\ns3_region = "garage"\napi_bind_addr = "[::]:3900"\n'
        ).encode(),
    )
    compose = [
        "docker",
        "compose",
        "-p",
        f"filmiq-attachment-{suffix}",
        "-f",
        str(directory / "compose.yaml"),
    ]
    config = json.loads(call([*compose, "config", "--format", "json"]))
    check_config(config, directory)
    fixture = (TEMPLATE / "fixture.cjs").read_bytes()
    try:
        call(
            [
                *compose,
                "up",
                "-d",
                "--no-deps",
                "--pull",
                "never",
                "source-db",
                "source-garage",
                "restored-db",
            ]
        )
        for service in ("source-db", "restored-db"):
            wait(compose, service, ["pg_isready", "-U", "kaneo", "-d", "kaneo"], service)
        wait(
            compose,
            "source-garage",
            ["/garage", "bucket", "info", "fictional-attachments"],
            "source object store",
        )
        call([*compose, "up", "-d", "--no-deps", "--pull", "never", "source-app"])
        print(
            call([*compose, "exec", "-T", "source-app", "node", "-", "create"], input_bytes=fixture)
            .decode()
            .strip(),
            flush=True,
        )
        call([*compose, "stop", "source-app", "source-garage"])
        dump = call([*compose, "exec", "-T", "source-db", "pg_dump", "-U", "kaneo", "-Fc", "kaneo"])
        save(directory / "backup/database.dump", dump)
        shutil.copytree(directory / "source-garage", directory / "backup/garage")
        source_hashes = digest_tree(directory / "source-garage")
        if not source_hashes or source_hashes != digest_tree(directory / "backup/garage"):
            raise RuntimeError("Fictional object-store backup mismatch")
        shutil.copytree(directory / "backup/garage", directory / "restored-garage")
        if source_hashes != digest_tree(directory / "restored-garage"):
            raise RuntimeError("Fictional object-store restore copy mismatch")
        count = call(
            [
                *compose,
                "exec",
                "-T",
                "restored-db",
                "psql",
                "-U",
                "kaneo",
                "-d",
                "kaneo",
                "-Atc",
                "SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND c.relkind IN ('r','p');",
            ]
        )
        if count.strip() != b"0":
            raise RuntimeError("Fictional destination database is not empty")
        call(
            [
                *compose,
                "exec",
                "-T",
                "restored-db",
                "pg_restore",
                "-U",
                "kaneo",
                "-d",
                "kaneo",
                "--exit-on-error",
            ],
            input_bytes=dump,
        )
        call([*compose, "up", "-d", "--no-deps", "--pull", "never", "empty-garage"])
        wait(
            compose,
            "empty-garage",
            ["/garage", "bucket", "info", "fictional-attachments"],
            "empty object store",
        )
        call([*compose, "up", "-d", "--no-deps", "--pull", "never", "restored-app"])
        print(
            call(
                [*compose, "exec", "-T", "restored-app", "node", "-", "missing"],
                input_bytes=fixture,
            )
            .decode()
            .strip(),
            flush=True,
        )
        call([*compose, "stop", "restored-app", "empty-garage"])
        call([*compose, "up", "-d", "--no-deps", "--pull", "never", "restored-garage"])
        wait(
            compose,
            "restored-garage",
            ["/garage", "bucket", "info", "fictional-attachments"],
            "restored object store",
        )
        call([*compose, "start", "restored-app"])
        print(
            call(
                [*compose, "exec", "-T", "restored-app", "node", "-", "verify"], input_bytes=fixture
            )
            .decode()
            .strip(),
            flush=True,
        )
        call([*compose, "stop", "restored-app"])
        call([*compose, "restart", "restored-garage"])
        wait(
            compose,
            "restored-garage",
            ["/garage", "bucket", "info", "fictional-attachments"],
            "restarted object store",
        )
        call([*compose, "start", "restored-app"])
        print(
            call(
                [*compose, "exec", "-T", "restored-app", "node", "-", "verify"], input_bytes=fixture
            )
            .decode()
            .strip(),
            flush=True,
        )
        print(f"Fixture and backups retained under {directory.relative_to(ROOT)}", flush=True)
    finally:
        stopped = subprocess.run([*compose, "stop"], capture_output=True, timeout=120, check=False)
        if stopped.returncode:
            raise RuntimeError("Fictional containers may still be running; inspect the fixture")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print(f"Fictional rehearsal stopped: {error}", file=sys.stderr)
        raise SystemExit(1) from None
