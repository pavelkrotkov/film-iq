"""Exercise the private importer using fictional records only."""

import argparse
import http.cookiejar
import json
import urllib.parse
import urllib.request
from pathlib import Path
from unittest.mock import patch

import kaneo_private_import
from kaneo_private_import import import_films
from kaneo_smoke import call


def synthetic_manifest() -> dict:
    films = []
    for ident, watched in ((900000001, False), (900000002, True)):
        films.append(
            {
                "tmdb_id": ident,
                "title": f"Fictional importer film {ident}",
                "source_year": 2001,
                "director": "Fictional director",
                "field_provenance": {"tmdb_id": "synthetic test identity"},
                "watched": watched,
                "watched_dates": [None] if watched else [],
                "accepted_discovery_evidence": {
                    "tmdb_id": ident,
                    "status": "available",
                    "links": [{"url": "https://example.invalid/ballot", "kind": "list"}],
                },
            }
        )
    return {"version": "tracker-poc-private-film-input-v1", "films": films}


def run(base: str, directory: Path) -> None:
    cookies = http.cookiejar.MozillaCookieJar(str(directory / "kaneo-cookies.txt"))
    cookies.load(ignore_discard=True)
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookies))
    workspace = json.loads((directory / "kaneo-ids.json").read_text())["workspace"]
    query = urllib.parse.urlencode({"workspaceId": workspace})
    projects = call(opener, base, f"/project?{query}")
    matches = [p for p in projects if p["name"] == "FilmIQ Import Test Fixtures"]
    if len(matches) > 1:
        raise ValueError("ambiguous synthetic test project")
    project = (
        matches[0]
        if matches
        else call(
            opener,
            base,
            "/project",
            {
                "name": "FilmIQ Import Test Fixtures",
                "workspaceId": workspace,
                "icon": "🎬",
                "slug": "filmiq-import-test-fixtures",
            },
        )
    )
    ident = project["id"]
    fixture = synthetic_manifest()
    first = import_films(opener, base, ident, fixture)
    task = first["mapping"]["900000001"]
    definitions = call(opener, base, f"/custom-field/project/{ident}")
    fields = {row["name"]: row["id"] for row in definitions}
    assert not any("watched" in name.lower() or "watchlist" in name.lower() for name in fields)
    marker = "User-edited fictional synopsis"
    call(opener, base, f"/task/description/{task}", {"description": marker}, "PUT")
    call(opener, base, f"/task/status/{task}", {"status": "in-progress"}, "PUT")
    altered_evidence = '{"user_edited":true}'
    call(
        opener,
        base,
        "/custom-field/value",
        {"taskId": task, "fieldId": fields["POC Evidence"], "value": altered_evidence},
        "PUT",
    )
    second = import_films(opener, base, ident, fixture)
    assert second["created"] == 0 and first["mapping"] == second["mapping"]
    record = call(opener, base, f"/task/{task}")
    assert record["description"] == marker and record["status"] == "in-progress"
    values = {
        row["fieldId"]: row["value"] for row in call(opener, base, f"/custom-field/task/{task}")
    }
    assert values[fields["POC Evidence"]] == altered_evidence
    assert values[fields["POC Source Year"]] == "2001"
    invalid = synthetic_manifest()
    invalid["films"].append(invalid["films"][0])
    try:
        import_films(opener, base, ident, invalid)
    except ValueError:
        pass
    else:
        raise AssertionError("Duplicate input identity was not rejected")
    retry_fixture = synthetic_manifest()
    additional = dict(retry_fixture["films"][0])
    additional["tmdb_id"] = 900000003
    additional["accepted_discovery_evidence"] = {
        "tmdb_id": 900000003,
        "status": "unknown",
        "links": [],
    }
    retry_fixture["films"].append(additional)
    original_call = kaneo_private_import.call
    raised = False

    def lost_response(opener, base: str, path: str, payload=None, method=None):
        nonlocal raised
        result = original_call(opener, base, path, payload, method)
        if path == f"/task/{ident}" and payload is not None and not raised:
            raised = True
            raise TimeoutError("synthetic lost response after create")
        return result

    # Use a unique synthetic ID on repeat runs so the failure occurs after create.
    existing = call(opener, base, f"/custom-field/project/{ident}/values")
    existing_ids = {row["value"] for row in existing if row["fieldId"] == fields["POC TMDB ID"]}
    while str(additional["tmdb_id"]) in existing_ids:
        additional["tmdb_id"] += 1
        additional["accepted_discovery_evidence"]["tmdb_id"] = additional["tmdb_id"]
    with patch.object(kaneo_private_import, "call", lost_response):
        try:
            import_films(opener, base, ident, retry_fixture)
        except TimeoutError:
            pass
        else:
            raise AssertionError("Synthetic response loss was not exercised")
    recovered = import_films(opener, base, ident, retry_fixture)
    assert recovered["created"] == 0 and len(recovered["mapping"]) == 3
    print("Synthetic Kaneo import, retry, edit preservation and duplicate rejection passed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="http://localhost:15173")
    parser.add_argument("--directory", type=Path, required=True)
    args = parser.parse_args()
    run(args.base.rstrip("/"), args.directory)
