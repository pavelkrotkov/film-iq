"""Set up an isolated local Kaneo workspace and verify synthetic access denial."""

import argparse
import http.cookiejar
import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit

from kaneo_smoke import call, ensure_field

from film_iq.personal_io import private_json


def setup(base: str, directory: Path) -> dict:
    cookies = http.cookiejar.MozillaCookieJar(str(directory / "kaneo-cookies.txt"))
    cookies.load(ignore_discard=True)
    owner = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookies))
    viewer = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar())
    )
    credentials = json.loads((directory / "kaneo-viewer.json").read_text())
    call(viewer, base, "/auth/sign-in/email", credentials)
    workspaces = call(owner, base, "/workspace")
    matches = [item for item in workspaces if item["name"] == "FilmIQ Private Input POC"]
    if len(matches) > 1:
        raise ValueError("ambiguous private workspace")
    workspace = (
        matches[0]
        if matches
        else call(
            owner,
            base,
            "/auth/organization/create",
            {"name": "FilmIQ Private Input POC", "slug": "filmiq-private-input-poc"},
        )
    )
    workspace_id = workspace["id"]
    query = urllib.parse.urlencode({"workspaceId": workspace_id})
    projects = call(owner, base, f"/project?{query}")

    def project(name: str, slug: str) -> dict:
        matches = [item for item in projects if item["name"] == name]
        if len(matches) > 1:
            raise ValueError("ambiguous private project")
        item = (
            matches[0]
            if matches
            else call(
                owner,
                base,
                "/project",
                {"name": name, "workspaceId": workspace_id, "icon": "🎬", "slug": slug},
            )
        )
        if item.get("isPublic") is not False:
            raise ValueError("private project visibility could not be confirmed")
        return item

    probe_project = project("Private Access Test Fixtures", "private-access-test-fixtures")
    film_project = project("Private Film Records", "private-film-records")
    probe_project_id, project_id = probe_project["id"], film_project["id"]
    field_id = ensure_field(owner, base, probe_project_id, "POC Fixture ID", "text")
    rows = call(owner, base, f"/custom-field/project/{probe_project_id}/values")
    existing = [r["taskId"] for r in rows if r["fieldId"] == field_id and r["value"] == "probe"]
    if len(existing) > 1:
        raise ValueError("duplicate access-test fixture")
    probe = (
        existing[0]
        if existing
        else call(
            owner,
            base,
            f"/task/{probe_project_id}",
            {
                "title": "Fictional private-access probe",
                "description": "Synthetic test only",
                "priority": "no-priority",
                "status": "to-do",
                "customFields": [{"fieldId": field_id, "value": "probe"}],
            },
        )["id"]
    )
    for path in (f"/task/{probe}", f"/custom-field/project/{project_id}"):
        try:
            call(viewer, base, path)
        except urllib.error.HTTPError as error:
            if error.code not in (401, 403, 404):
                raise
        else:
            raise PermissionError("outside-workspace viewer unexpectedly has project access")
    return {"workspace": workspace_id, "project": project_id}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="http://localhost:15173")
    parser.add_argument("--directory", required=True, type=Path)
    args = parser.parse_args()
    parsed = urlsplit(args.base)
    if parsed.scheme != "http" or parsed.hostname not in ("localhost", "127.0.0.1"):
        raise ValueError("This experiment only supports a local loopback instance")
    result = setup(args.base.rstrip("/"), args.directory)
    private = args.directory / "private"
    private.mkdir(mode=0o700, parents=True, exist_ok=True)
    private_json(private / "kaneo-private-ids.json", result)
    print("Private projects ready; outside-workspace viewer access was rejected")


if __name__ == "__main__":
    main()
