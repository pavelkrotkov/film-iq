"""Run real enrichment code against the isolated fictional recovery instance.

The fixture API session is freshly created inside its container and never
comes from a browser. This test does not contact a metadata provider or read
any live project, preference, or Movary data. Each run leaves a fictional task.
"""

import argparse
import json
import re
import secrets
import select
import subprocess
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

import kaneo_enrich
import kaneo_smoke
from enrichment import FixtureSource, enrich

ROOT = Path(__file__).resolve().parents[3]
RPC = ROOT / "docs/research/tracker-poc/kaneo-recovery-fixture/enrichment-rpc.js"
APP_IMAGE = "ghcr.io/usekaneo/kaneo:2.49.0@sha256:cd1826b1aba3ce736015cadf6f6c975d923aac00f4b6aaa7aedb29bc722dae49"
DB_IMAGE = (
    "postgres:16-alpine@sha256:0cefaabd882e42bcb2a2f3dc56d3ce4770560ba62fd7f197f1a2e008fd5731ab"
)


def inspect(*args: str) -> dict:
    output = subprocess.check_output(["docker", "inspect", *args], text=True, timeout=20)
    rows = json.loads(output)
    if not isinstance(rows, list) or len(rows) != 1:
        raise ValueError("Fixture inspection failed")
    return rows[0]


def isolated(app: str) -> None:
    match = re.fullmatch(r"(filmiq-recovery-([0-9a-f]{12}))\-source-app-1", app)
    if not match:
        raise ValueError("Expected the named fictional recovery fixture")
    project, suffix = match.groups()
    application = inspect(app)
    database = inspect(f"{project}-source-db-1")
    network_name = f"{project}_source"
    network = inspect("--type=network", network_name)
    db_mount = ROOT / f".cache/tracker-poc/recovery-replay-{suffix}/source-db"
    mounts = database.get("Mounts", [])
    if (
        application["Config"]["Image"] != APP_IMAGE
        or database["Config"]["Image"] != DB_IMAGE
        or not application["State"]["Running"]
        or not database["State"]["Running"]
        or application.get("Mounts")
        or set(application["NetworkSettings"]["Networks"]) != {network_name}
        or set(database["NetworkSettings"]["Networks"]) != {network_name}
        or network.get("Internal") is not True
        or len(mounts) != 1
        or Path(mounts[0].get("Source", "")).resolve() != db_mount.resolve()
        or mounts[0].get("Destination") != "/var/lib/postgresql/data"
    ):
        raise ValueError("Fictional fixture isolation check failed")


class FixtureAPI:
    def __init__(self, app: str):
        self.process = subprocess.Popen(
            ["docker", "exec", "-i", app, "node", "-e", RPC.read_text()],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        try:
            if self.read() != {"ready": True}:
                raise RuntimeError("Fictional API authentication failed")
        except Exception:
            self.close()
            raise

    def read(self):
        if self.process.stdout is None or not select.select([self.process.stdout], [], [], 40)[0]:
            raise RuntimeError("Fictional API did not respond")
        return json.loads(self.process.stdout.readline())

    def call(self, _opener, _base, path: str, payload=None, method=None):
        if self.process.stdin is None:
            raise RuntimeError("Fictional API unavailable")
        self.process.stdin.write(
            json.dumps({"path": path, "body": payload, "method": method}) + "\n"
        )
        self.process.stdin.flush()
        result = self.read()
        if not isinstance(result, dict) or result.get("ok") is not True:
            raise RuntimeError("Fictional API request failed")
        return result["data"]

    def close(self) -> None:
        if self.process.stdin:
            self.process.stdin.close()
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.terminate()
            self.process.wait(timeout=5)
        if self.process.stdout:
            self.process.stdout.close()


class Offers(FixtureSource):
    def __init__(self, *, changed=False, partial=False, failed=False):
        self.changed, self.partial, self.failed = changed, partial, failed

    def availability(self, source_id: int) -> dict | None:
        if self.failed:
            raise RuntimeError("fictional source failure")
        return {
            "id": source_id,
            "results": {
                "US": {
                    "link": "https://example.invalid/fictional",
                    "flatrate": [{}]
                    if self.partial
                    else [
                        {
                            "provider_id": 1,
                            "provider_name": "Stream B" if self.changed else "Stream A",
                        }
                    ],
                    "rent": [{"provider_id": 2, "provider_name": "Rental A"}],
                    "buy": [{"provider_id": 3, "provider_name": "Purchase A"}],
                }
            },
        }


def check(app: str) -> None:
    isolated(app)
    api = FixtureAPI(app)
    try:
        with (
            patch.object(kaneo_smoke, "call", api.call),
            patch.object(kaneo_enrich, "call", api.call),
        ):
            workspaces = api.call(None, "", "/workspace")
            workspace = next(
                row for row in workspaces if row["name"] == "Fictional Recovery Workspace"
            )
            projects = api.call(None, "", f"/project?workspaceId={workspace['id']}")
            project = next(row for row in projects if row["name"] == "Fictional Films")
            backend = kaneo_enrich.KaneoBackend.__new__(kaneo_enrich.KaneoBackend)
            backend.base, backend.project = "fixture", project["id"]
            backend.opener = urllib.request.build_opener()
            backend.fields = {
                key: kaneo_smoke.ensure_field(None, "fixture", backend.project, name, kind)
                for key, name, kind in (
                    ("identity", "POC Synthetic External ID", "text"),
                    ("year", "POC Year", "number"),
                    ("genre", "POC Genre", "text"),
                    ("availability", "POC Synthetic Availability", "text"),
                )
            }
            rows = api.call(None, "", f"/custom-field/project/{backend.project}/values")
            used = {row["value"] for row in rows if row["fieldId"] == backend.fields["identity"]}
            identity = 1_000_000_000 + secrets.randbelow(1_000_000_000)
            while str(identity) in used:
                identity = 1_000_000_000 + secrets.randbelow(1_000_000_000)
            now = datetime.now(UTC)
            record = enrich(Offers(), backend, identity, now)
            assert enrich(Offers(), backend, identity, now) == record
            api.call(
                None,
                "",
                f"/task/description/{record}",
                {"description": "Fictional edited synopsis."},
                "PUT",
            )
            api.call(None, "", f"/task/status/{record}", {"status": "in-progress"}, "PUT")

            def read():
                fields = api.call(None, "", f"/custom-field/task/{record}")
                values = {row["fieldId"]: row["value"] for row in fields}
                return json.loads(values[backend.fields["availability"]])

            initial = read()
            assert initial["subscription"] == ["Stream A"]
            assert initial["rent"] == ["Rental A"] and initial["buy"] == ["Purchase A"]
            assert enrich(Offers(changed=True), backend, identity, now) == record
            latest = read()
            assert latest["subscription"] == ["Stream B"]
            assert latest["rent"] == ["Rental A"] and latest["buy"] == ["Purchase A"]
            assert enrich(Offers(partial=True), backend, identity, now) == record
            try:
                enrich(Offers(failed=True), backend, identity, now)
            except RuntimeError:
                pass
            else:
                raise AssertionError("Source failure was not raised")
            assert read() == latest
            task = api.call(None, "", f"/task/{record}")
            assert (
                task["description"] == "Fictional edited synopsis."
                and task["status"] == "in-progress"
            )
            rows = api.call(None, "", f"/custom-field/project/{backend.project}/values")
            assert (
                sum(
                    row["fieldId"] == backend.fields["identity"] and row["value"] == str(identity)
                    for row in rows
                )
                == 1
            )
    finally:
        api.close()
    print("Fictional Kaneo import, repeat, category refresh and failure preservation passed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture-app", required=True)
    check(parser.parse_args().fixture_app)
