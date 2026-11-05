"""Check one fresh private import without printing film or account contents."""

import argparse
import http.cookiejar
import json
import urllib.error
import urllib.request
from pathlib import Path

from kaneo_private_import import PUBLIC_FIELD_PROVENANCE, PUBLIC_IDENTITY_PROVENANCE, validate
from kaneo_smoke import call


def run(base: str, directory: Path) -> None:
    private = directory / "private"
    project = json.loads((private / "kaneo-private-ids.json").read_text())["project"]
    manifest = json.loads((private / "film-input.json").read_text())
    validate(manifest)
    cookies = http.cookiejar.MozillaCookieJar(str(directory / "kaneo-cookies.txt"))
    cookies.load(ignore_discard=True)
    owner = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookies))
    definitions = call(owner, base, f"/custom-field/project/{project}")
    rows = call(owner, base, f"/custom-field/project/{project}/values")
    by_id = verify_records(manifest, definitions, rows)
    viewer = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar())
    )
    call(
        viewer,
        base,
        "/auth/sign-in/email",
        json.loads((directory / "kaneo-viewer.json").read_text()),
    )
    task = next(iter(by_id.values()))[0]
    verify_viewer_denied(viewer, base, task)
    print(f"Verified {len(by_id)} unique records; source fields and viewer isolation passed")


def verify_records(manifest: dict, definitions: list, rows: list) -> dict:
    """Validate shared fields without replacing or exposing private input values."""
    validate(manifest)
    fields = {row["name"]: row["id"] for row in definitions}
    if len(fields) != len(definitions):
        raise ValueError("duplicate custom field names")
    if any("watched" in name.lower() or "watchlist" in name.lower() for name in fields):
        raise ValueError("personal watched or watchlist field exists in canonical project")
    values = {}
    for row in rows:
        task_values = values.setdefault(row["taskId"], {})
        if row["fieldId"] in task_values:
            raise ValueError("duplicate custom field values")
        task_values[row["fieldId"]] = row["value"]
    by_id = {}
    for task, data in values.items():
        identity = data.get(fields["POC TMDB ID"])
        if identity:
            if identity in by_id:
                raise ValueError("duplicate tracker identity")
            by_id[identity] = (task, data)
    if set(by_id) != {str(film["tmdb_id"]) for film in manifest["films"]}:
        raise ValueError("tracker identity set differs from manifest")
    for film in manifest["films"]:
        _, data = by_id[str(film["tmdb_id"])]
        if data.get(fields["POC Identity Provenance"]) != PUBLIC_IDENTITY_PROVENANCE:
            raise ValueError("identity provenance is not category-neutral")
        if data.get(fields["POC Field Provenance"]) != PUBLIC_FIELD_PROVENANCE:
            raise ValueError("field provenance is not category-neutral")
        if json.loads(data[fields["POC Evidence"]]) != film["accepted_discovery_evidence"]:
            raise ValueError("source evidence failed readback")
        expected_year = str(film["source_year"]) if film.get("source_year") else None
        if data.get(fields["POC Source Year"]) != expected_year:
            raise ValueError("source year failed readback")
        if data.get(fields["POC Source Director"]) != (film.get("director") or None):
            raise ValueError("source director failed readback")
    return by_id


def verify_viewer_denied(viewer, base: str, task: str) -> None:
    try:
        call(viewer, base, f"/task/{task}")
    except urllib.error.HTTPError as error:
        if error.code not in (401, 403, 404):
            raise
    else:
        raise PermissionError("outside-workspace viewer unexpectedly read a private film")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="http://localhost:15173")
    parser.add_argument("--directory", required=True, type=Path)
    args = parser.parse_args()
    run(args.base.rstrip("/"), args.directory)
