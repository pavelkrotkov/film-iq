"""Check an isolated fictional watchlist property on local pinned YouTrack.

The source hash must be independently reviewed before running. This installs a
separate app and leaves it installed; it does not touch the FilmIQ app, Movary,
tracker issues, or the FilmIQ user properties.
"""

import argparse
import hashlib
import json
import os
import re
import secrets
import subprocess
import sys

from youtrack_client import ROOT, YouTrackClient, YouTrackError

NAME = "filmiq-watchlist-live-fixture"
PROP = "fixtureFilmMovaryWatchlist"
SOURCE = ROOT / "docs/research/tracker-poc/youtrack-app/movary-watchlist.js"
PRIVATE = ROOT / ".cache/tracker-poc/private"
CLI = ROOT / ".cache/tracker-poc/youtrack-tools/node_modules/.bin/youtrack-app"


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def run(expected):
    require(re.fullmatch(r"[0-9a-f]{64}", expected), "Expected source SHA-256")
    source = SOURCE.read_text(encoding="utf-8")
    require(digest(source.encode()) == expected, "Source does not match reviewed hash")
    require(source.count("const PROJECTS = ['FILMPOC', 'FILMREAL'];") == 1, "Project guard absent")
    require(source.count("filmMovaryWatchlist") == 3, "Unexpected property references")
    isolated = source.replace(
        "const PROJECTS = ['FILMPOC', 'FILMREAL'];", "const PROJECTS = ['FILMPOC'];"
    )
    isolated = isolated.replace("filmMovaryWatchlist", PROP)
    require(
        "FILMREAL" not in isolated and "filmMovaryWatchlist" not in isolated, "Isolation failed"
    )
    client = YouTrackClient()
    require(
        client.request("users/me", query={"fields": "login"}).get("login") == "admin",
        "Unexpected user",
    )
    env = os.environ.copy()
    env["YOUTRACK_HOST"] = "http://localhost:18180"
    env["YOUTRACK_TOKEN"] = (PRIVATE / "youtrack-token").read_text().strip()

    def cli(*args):
        result = subprocess.run(
            [str(CLI), *args], env=env, capture_output=True, text=True, timeout=90
        )
        require(result.returncode == 0, "Official app CLI failed")
        return result.stdout

    apps = json.loads(cli("app", "list", "--limit", "100", "--json"))
    require(
        not apps.get("pagination", {}).get("hasMore")
        and all(item.get("name") != NAME for item in apps.get("items", [])),
        "Fixture app name not free",
    )

    def baseline():
        state = {
            "watched": client.request("extensionEndpoints/filmiq-poc/movary/property-export"),
            "preferences": client.request("extensionEndpoints/filmiq-poc/preferences/all"),
        }
        for action in ("settings", "usages"):
            state[action] = json.loads(cli("app", action, "--app", "filmiq-poc", "--json"))
        return digest(json.dumps(state, sort_keys=True, separators=(",", ":")).encode())

    main_baseline = baseline()

    def unchanged():
        require(baseline() == main_baseline, "Main app baseline changed")

    folder = PRIVATE / ("watchlist-live-fixture-" + secrets.token_hex(6))
    folder.mkdir(mode=0o700, parents=True, exist_ok=False)
    manifest = {
        "name": NAME,
        "title": "Fictional watchlist fixture",
        "description": "Fictional FILMPOC-only test",
        "version": "0.1.0",
        "minYouTrackVersion": "2026.2.0",
    }
    extensions = {
        "entityTypeExtensions": [{"entityType": "User", "properties": {PROP: {"type": "string"}}}]
    }
    for name, value in [
        ("manifest.json", json.dumps(manifest)),
        ("entity-extensions.json", json.dumps(extensions)),
        ("movary-watchlist.js", isolated),
    ]:
        path = folder / name
        path.write_text(value, encoding="utf-8")
        path.chmod(0o600)
    require(
        SOURCE.read_bytes() == source.encode()
        and (folder / "movary-watchlist.js").read_text() == isolated,
        "Source changed",
    )
    cli("app", "upload", "--directory", str(folder))
    unchanged()
    endpoint = "extensionEndpoints/" + NAME + "/movary-watchlist/"

    def get(path, **query):
        return client.request(endpoint + path, query=query or None)

    def post(path, body):
        return client.request(endpoint + path, body=body)

    def rejected(path, body, code):
        try:
            post(path, body)
        except YouTrackError as exc:
            require(str(exc).endswith("returned HTTP " + str(code)), "Unexpected rejection")
        else:
            raise RuntimeError("Expected rejection did not occur")

    before = get("property-export")
    require(before.get("raw") is None, "Fixture property is not empty")
    require(
        get("list", project="FILMPOC")
        == {"status": "unknown", "source": "Movary", "observed_at": None, "entries": []},
        "Initial property unavailable",
    )
    try:
        get("list", project="FILMREAL")
    except YouTrackError as exc:
        require(str(exc).endswith("returned HTTP 400"), "Unexpected project rejection")
    else:
        raise RuntimeError("Accepted a non-fixture project")
    snapshot = {
        "version": "tracker-poc-movary-watchlist-v1",
        "source": "Movary",
        "project": "FILMPOC",
        "observed_at": "2026-11-06T12:00:00+00:00",
        "entries": [
            {
                "tmdb_id": 1900000001,
                "title": "Fictional fixture film",
                "added_at": "2026-11-01 09:02:03",
            }
        ],
    }
    body = {"owner": before["owner"], "expected": before["raw"], "snapshot": snapshot}
    require(post("import", body) == {"status": "imported", "entries": 1}, "Import failed")
    unchanged()
    after = get("property-export")
    require(
        get("list", project="FILMPOC")
        == {
            "status": "available",
            "source": "Movary",
            "observed_at": snapshot["observed_at"],
            "entries": snapshot["entries"],
        },
        "Readback failed",
    )
    rejected("import", body, 409)
    require(
        post("import", {**body, "expected": after["raw"]}) == {"status": "unchanged", "entries": 1},
        "Idempotent retry failed",
    )
    rejected(
        "import", {**body, "expected": after["raw"], "snapshot": {**snapshot, "entries": []}}, 409
    )
    rejected(
        "import",
        {
            **body,
            "expected": after["raw"],
            "snapshot": {**snapshot, "observed_at": "2026-11-05T12:00:00+00:00"},
        },
        409,
    )
    rejected("property-restore", {"expected": before, "backup": before}, 409)
    require(
        post("property-restore", {"expected": after, "backup": before}) == {"status": "restored"},
        "Restore failed",
    )
    require(
        get("property-export") == before and get("list", project="FILMPOC")["status"] == "unknown",
        "Restore readback failed",
    )
    unchanged()
    print(
        "Fictional isolated app: project check, import, readback, stale guards and restore passed"
    )
    print(
        "Separate app retained; restricted-user permission denial remains covered by the offline fixture only"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reviewed-source-sha256", required=True)
    try:
        run(parser.parse_args().reviewed_source_sha256)
    except Exception as exc:
        print(
            "Isolated fixture stopped:",
            type(exc).__name__,
            str(exc) if isinstance(exc, RuntimeError) else "",
            file=sys.stderr,
        )
        sys.exit(1)
