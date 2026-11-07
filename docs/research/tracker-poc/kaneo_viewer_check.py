"""Verify a synthetic viewer can read but cannot edit the test film."""

import argparse
import http.cookiejar
import json
import secrets
import urllib.error
import urllib.request
from pathlib import Path

from kaneo_bootstrap import private_json
from kaneo_smoke import call


def check(base: str, directory: Path):
    ids = json.loads((directory / "kaneo-ids.json").read_text())
    credentials_file = directory / "kaneo-viewer.json"
    if not credentials_file.exists():
        private_json(
            credentials_file,
            {
                "name": "POC Viewer",
                "email": "poc-b@example.invalid",
                "password": secrets.token_urlsafe(24),
            },
        )
    credentials = json.loads(credentials_file.read_text())
    viewer = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar())
    )
    try:
        user = call(viewer, base, "/auth/sign-in/email", credentials)["user"]
    except urllib.error.HTTPError as error:
        if error.code not in (400, 401):
            raise
        user = call(viewer, base, "/auth/sign-up/email", credentials)["user"]

    admin_cookies = http.cookiejar.MozillaCookieJar(str(directory / "kaneo-cookies.txt"))
    admin_cookies.load(ignore_discard=True)
    admin = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(admin_cookies))
    members_path = f"/admin/workspaces/{ids['workspace']}/members"
    members = call(admin, base, members_path)
    member = next((row for row in members if row["userId"] == user["id"]), None)
    if member is None:
        call(admin, base, members_path, {"userId": user["id"], "role": "viewer"})
    elif member["role"] != "viewer":
        raise ValueError("synthetic user already has a different role")

    values = call(admin, base, f"/custom-field/project/{ids['project']}/values")
    matches = [
        row["taskId"]
        for row in values
        if row["fieldName"] == "POC Fixture ID" and row["value"] == "fixture-0001"
    ]
    if len(matches) != 1:
        raise ValueError("run the Kaneo smoke test first; fixture must be unique")
    task = matches[0]
    before = call(admin, base, f"/task/{task}")["description"]
    assert call(viewer, base, f"/task/{task}")["id"] == task
    try:
        call(
            viewer,
            base,
            f"/task/description/{task}",
            {"description": "unauthorized viewer change"},
            "PUT",
        )
    except urllib.error.HTTPError as error:
        assert error.code == 403
    else:
        raise AssertionError("viewer unexpectedly modified the record")
    assert call(admin, base, f"/task/{task}")["description"] == before
    print("Synthetic viewer read succeeded, update returned 403, original description preserved")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="http://localhost:15173")
    parser.add_argument("--directory", required=True, type=Path)
    args = parser.parse_args()
    check(args.base.rstrip("/"), args.directory)
