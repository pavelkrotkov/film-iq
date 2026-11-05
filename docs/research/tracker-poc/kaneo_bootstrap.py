"""Create an isolated synthetic Kaneo user, workspace and Films project.

Only run against a new dedicated local POC instance. Credentials and the cookie
jar are written under the supplied project-local directory with mode 0600.
"""

import argparse
import http.cookiejar
import json
import os
import secrets
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from kaneo_smoke import call


def private_json(path: Path, payload: dict):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as output:
        json.dump(payload, output)


def bootstrap(base: str, directory: Path):
    directory.mkdir(parents=True, exist_ok=True)
    credentials_file = directory / "kaneo-test-user.json"
    if not credentials_file.exists():
        private_json(
            credentials_file,
            {
                "name": "POC User A",
                "email": "poc-a@example.invalid",
                "password": secrets.token_urlsafe(24),
            },
        )
    credentials = json.loads(credentials_file.read_text())
    jar_file = directory / "kaneo-cookies.txt"
    cookies = http.cookiejar.MozillaCookieJar(str(jar_file))
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookies))
    try:
        call(opener, base, "/auth/sign-in/email", credentials)
    except urllib.error.HTTPError as error:
        if error.code not in (400, 401):
            raise
        call(opener, base, "/auth/sign-up/email", credentials)
    fd = os.open(jar_file, os.O_WRONLY | os.O_CREAT, 0o600)
    os.close(fd)
    jar_file.chmod(0o600)
    cookies.save(ignore_discard=True)
    workspaces = call(opener, base, "/workspace")
    workspace = next((item for item in workspaces if item["name"] == "Film POC"), None)
    if workspace is None:
        workspace = call(
            opener, base, "/auth/organization/create", {"name": "Film POC", "slug": "film-poc"}
        )
    query = urllib.parse.urlencode({"workspaceId": workspace["id"]})
    projects = call(opener, base, f"/project?{query}")
    project = next((item for item in projects if item["name"] == "Films"), None)
    if project is None:
        project = call(
            opener,
            base,
            "/project",
            {"name": "Films", "workspaceId": workspace["id"], "icon": "🎬", "slug": "films"},
        )
    ids = directory / "kaneo-ids.json"
    ids.write_text(json.dumps({"workspace": workspace["id"], "project": project["id"]}))
    print(f"Films project: {project['id']}; credentials and session are stored privately")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="http://localhost:15173")
    parser.add_argument("--directory", required=True, type=Path)
    args = parser.parse_args()
    bootstrap(args.base.rstrip("/"), args.directory)
