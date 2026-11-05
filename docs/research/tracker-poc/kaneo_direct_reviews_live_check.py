"""Exercise review imports in an isolated project using new fictional films only."""

import argparse
import json
import secrets
import urllib.error
from pathlib import Path
from urllib.parse import urlencode

from kaneo_direct_reviews import import_reviews
from kaneo_smoke import call, ensure_field
from preferences_check import login


def run(directory: Path) -> None:
    base = "http://localhost:15173"
    workspace = json.loads((directory / "kaneo-ids.json").read_text())["workspace"]
    owner = login(directory / "kaneo-test-user.json")
    viewer = login(directory / "kaneo-viewer.json")
    projects = call(owner, base, "/project?" + urlencode({"workspaceId": workspace}))
    matches = [p for p in projects if p["name"] == "FilmIQ Review Link Test Fixtures"]
    if len(matches) > 1:
        raise ValueError("ambiguous test project")
    project = (
        matches[0]
        if matches
        else call(
            owner,
            base,
            "/project",
            {
                "name": "FilmIQ Review Link Test Fixtures",
                "workspaceId": workspace,
                "icon": "🎬",
                "slug": "filmiq-review-link-fixtures",
            },
        )
    )
    project_id = project["id"]
    fields = {
        name: ensure_field(owner, base, project_id, name, "text")
        for name in ("POC TMDB ID", "POC Direct Review Links", "POC Evidence")
    }
    status = call(owner, base, f"/column/{project_id}")[0]["slug"]
    source = {"version": "tracker-poc-private-film-input-v1", "films": []}
    manifest = {"schema_version": 1, "films": []}
    tasks = []
    base_id = 4_000_000_000 + secrets.randbelow(1_000_000_000) * 10
    for offset in range(4):
        ident = base_id + offset
        title = f"Fictional Review Fixture {ident}"
        evidence = {
            "input_title": title,
            "source_page_title": title,
            "director": "Fictional Director",
            "input_source_year": 2001,
            "basis": "Synthetic fixture",
        }
        link = {
            "url": f"https://example.com/review/{ident}",
            "provider": "Example",
            "type": "individual_critic_review",
            "checked_at": "2026-11-05T12:00:00Z",
            "identity_evidence": evidence,
        }
        source["films"].append(
            {
                "tmdb_id": ident,
                "title": title,
                "director": "Fictional Director",
                "source_year": 2001,
                "origin": ["discovery"],
                "field_provenance": {"tmdb_id": "reviewed accepted identity match"},
            }
        )
        manifest["films"].append({"tmdb_id": ident, "links": [link]})
        custom = [
            {"fieldId": fields["POC TMDB ID"], "value": str(ident)},
            {"fieldId": fields["POC Evidence"], "value": "synthetic original evidence"},
        ]
        if offset == 1:
            custom.append(
                {
                    "fieldId": fields["POC Direct Review Links"],
                    "value": "synthetic user-edited value",
                }
            )
        task = call(
            owner,
            base,
            f"/task/{project_id}",
            {
                "title": title if offset != 2 else "Fictional corrected title",
                "description": "Synthetic original synopsis",
                "priority": "no-priority",
                "status": status,
                "customFields": custom,
            },
        )
        tasks.append(task["id"])
    try:
        call(
            viewer,
            base,
            "/custom-field/value",
            {
                "taskId": tasks[2],
                "fieldId": fields["POC Direct Review Links"],
                "value": "unauthorized",
            },
            "PUT",
        )
    except urllib.error.HTTPError as error:
        assert error.code == 403
    else:
        raise AssertionError("viewer unexpectedly wrote a review field")
    first_batch = {"schema_version": 1, "films": manifest["films"][:3]}
    second_batch = {"schema_version": 1, "films": manifest["films"][3:]}
    preview = import_reviews(owner, base, project_id, first_batch, source)
    assert preview == {"pending": 1, "skipped": 1, "conflicts": 1, "written": 0}
    result = import_reviews(owner, base, project_id, first_batch, source, apply=True)
    assert result == {"pending": 0, "skipped": 1, "conflicts": 1, "written": 1}
    assert import_reviews(owner, base, project_id, first_batch, source, apply=True) == {
        "pending": 0,
        "skipped": 2,
        "conflicts": 1,
        "written": 0,
    }
    first_value = next(
        v["value"]
        for v in call(owner, base, f"/custom-field/task/{tasks[0]}")
        if v["fieldId"] == fields["POC Direct Review Links"]
    )
    assert import_reviews(owner, base, project_id, second_batch, source, apply=True)["written"] == 1
    assert (
        next(
            v["value"]
            for v in call(owner, base, f"/custom-field/task/{tasks[0]}")
            if v["fieldId"] == fields["POC Direct Review Links"]
        )
        == first_value
    )
    for offset, task in enumerate(tasks):
        record = call(owner, base, f"/task/{task}")
        assert record["description"] == "Synthetic original synopsis" and record["status"] == status
        if offset == 2:
            assert record["title"] == "Fictional corrected title"
        values = {v["fieldId"]: v["value"] for v in call(owner, base, f"/custom-field/task/{task}")}
        assert values[fields["POC Evidence"]] == "synthetic original evidence"
        if offset == 1:
            assert values[fields["POC Direct Review Links"]] == "synthetic user-edited value"
        if offset == 2:
            assert fields["POC Direct Review Links"] not in values
    print(
        "Live fictional two-batch import, retry, edited-field/title preservation and viewer 403 passed"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    run(parser.parse_args().directory)
