"""Run a provenance migration only in a dedicated fictional Kaneo project."""

import argparse
import json
import secrets
from copy import deepcopy
from pathlib import Path
from urllib.parse import urlencode

from kaneo_private_import import PUBLIC_FIELD_PROVENANCE, PUBLIC_IDENTITY_PROVENANCE, import_films
from kaneo_private_verify import verify_records
from kaneo_provenance_migration import migrate
from kaneo_smoke import call
from preferences_check import login, preference_request


def run(directory: Path) -> None:
    base = "http://localhost:15173"
    workspace = json.loads((directory / "kaneo-ids.json").read_text())["workspace"]
    owner = login(directory / "kaneo-test-user.json")
    projects = call(owner, base, "/project?" + urlencode({"workspaceId": workspace}))
    matches = [p for p in projects if p["name"] == "FilmIQ Provenance Test Fixtures"]
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
                "name": "FilmIQ Provenance Test Fixtures",
                "workspaceId": workspace,
                "icon": "🎬",
                "slug": "filmiq-provenance-test-fixtures",
            },
        )
    )
    project_id = project["id"]
    manifest = {"version": "tracker-poc-private-film-input-v1", "films": []}
    base_id = 5_000_000_000 + secrets.randbelow(100_000_000) * 10
    for offset in range(3):
        ident = base_id + offset
        provenance = {
            "tmdb_id": f"synthetic-private-origin-{offset}",
            "title": f"synthetic-private-title-origin-{offset}",
        }
        manifest["films"].append(
            {
                "tmdb_id": ident,
                "title": f"Fictional Provenance Fixture {ident}",
                "source_year": 2001,
                "director": "Fictional Director",
                "field_provenance": provenance,
                "accepted_discovery_evidence": {"tmdb_id": ident, "status": "unknown", "links": []},
            }
        )
    original = deepcopy(manifest)
    created = import_films(owner, base, project_id, manifest)
    assert created["created"] == 3
    definitions = call(owner, base, f"/custom-field/project/{project_id}")
    fields = {field["name"]: field["id"] for field in definitions}
    tasks = [created["mapping"][str(film["tmdb_id"])] for film in manifest["films"]]
    for task in tasks:
        values = {v["fieldId"]: v["value"] for v in call(owner, base, f"/custom-field/task/{task}")}
        assert values[fields["POC Identity Provenance"]] == PUBLIC_IDENTITY_PROVENANCE
        assert values[fields["POC Field Provenance"]] == PUBLIC_FIELD_PROVENANCE
        assert "synthetic-private" not in json.dumps(values)
    for offset in (0, 1):
        provenance = manifest["films"][offset]["field_provenance"]
        for name, value in (
            ("POC Identity Provenance", provenance["tmdb_id"]),
            ("POC Field Provenance", json.dumps(provenance, ensure_ascii=False)),
        ):
            call(
                owner,
                base,
                "/custom-field/value",
                {"taskId": tasks[offset], "fieldId": fields[name], "value": value},
                "PUT",
            )
    call(
        owner,
        base,
        "/custom-field/value",
        {
            "taskId": tasks[1],
            "fieldId": fields["POC Field Provenance"],
            "value": "Synthetic manually edited field",
        },
        "PUT",
    )
    before = [call(owner, base, f"/task/{task}") for task in tasks]
    prefs_before = preference_request(owner, "/preferences")["preferences"]
    activity_before = call(owner, base, f"/activity/{tasks[0]}")
    assert migrate(owner, base, project_id, manifest) == {
        "pending": 1,
        "already": 1,
        "conflicts": 1,
        "updated": 0,
    }
    assert migrate(owner, base, project_id, manifest, apply=True) == {
        "pending": 0,
        "already": 1,
        "conflicts": 1,
        "updated": 1,
    }
    assert migrate(owner, base, project_id, manifest, apply=True) == {
        "pending": 0,
        "already": 2,
        "conflicts": 1,
        "updated": 0,
    }
    for index, task in enumerate(tasks):
        after = call(owner, base, f"/task/{task}")
        for key in ("title", "description", "status"):
            assert after[key] == before[index][key]
        values = {v["fieldId"]: v["value"] for v in call(owner, base, f"/custom-field/task/{task}")}
        if index == 1:
            assert values[fields["POC Field Provenance"]] == "Synthetic manually edited field"
        else:
            assert values[fields["POC Identity Provenance"]] == PUBLIC_IDENTITY_PROVENANCE
            assert values[fields["POC Field Provenance"]] == PUBLIC_FIELD_PROVENANCE
    clean_manifest = {**manifest, "films": [manifest["films"][0], manifest["films"][2]]}
    clean_tasks = {tasks[0], tasks[2]}
    project_values = call(owner, base, f"/custom-field/project/{project_id}/values")
    assert (
        len(
            verify_records(
                clean_manifest,
                definitions,
                [row for row in project_values if row["taskId"] in clean_tasks],
            )
        )
        == 2
    )
    assert preference_request(owner, "/preferences")["preferences"] == prefs_before
    assert manifest == original
    activity_after = call(owner, base, f"/activity/{tasks[0]}")
    assert len(activity_after) == len(activity_before)
    assert "synthetic-private-origin" not in json.dumps(activity_after)
    print("Synthetic neutral creation, migration, conflict, preference and activity checks passed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    run(parser.parse_args().directory)
