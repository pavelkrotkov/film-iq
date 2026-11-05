"""Check neutral provenance, untouched evidence, identities and viewer denial with fictional data."""

import json
import urllib.error
from copy import deepcopy
from email.message import Message
from unittest.mock import patch

from kaneo_private_import import PUBLIC_FIELD_PROVENANCE, PUBLIC_IDENTITY_PROVENANCE
from kaneo_private_import_check import synthetic_manifest
from kaneo_private_verify import verify_records, verify_viewer_denied


def run() -> None:
    manifest = synthetic_manifest()
    original = deepcopy(manifest)
    names = (
        "POC TMDB ID",
        "POC Identity Provenance",
        "POC Field Provenance",
        "POC Evidence",
        "POC Source Year",
        "POC Source Director",
    )
    definitions = [{"name": name, "id": name} for name in names]
    rows = []
    for film in manifest["films"]:
        task = str(film["tmdb_id"])
        values = {
            "POC TMDB ID": task,
            "POC Identity Provenance": PUBLIC_IDENTITY_PROVENANCE,
            "POC Field Provenance": PUBLIC_FIELD_PROVENANCE,
            "POC Evidence": json.dumps(film["accepted_discovery_evidence"]),
            "POC Source Year": str(film["source_year"]),
            "POC Source Director": film["director"],
        }
        rows.extend(
            {"taskId": task, "fieldId": field, "value": value} for field, value in values.items()
        )
    assert len(verify_records(manifest, definitions, rows)) == 2
    assert manifest == original
    for target in (
        "POC TMDB ID",
        "POC Identity Provenance",
        "POC Field Provenance",
        "POC Evidence",
        "POC Source Year",
        "POC Source Director",
    ):
        altered = deepcopy(rows)
        next(row for row in altered if row["fieldId"] == target)["value"] = "fictional modification"
        try:
            verify_records(manifest, definitions, altered)
        except (ValueError, json.JSONDecodeError):
            pass
        else:
            raise AssertionError(f"modified {target} passed verification")
    duplicated = deepcopy(rows)
    duplicated.append(deepcopy(rows[0]))
    try:
        verify_records(manifest, definitions, duplicated)
    except ValueError:
        pass
    else:
        raise AssertionError("duplicate tracker value passed verification")
    for status in (401, 403, 404):
        with patch(
            "kaneo_private_verify.call",
            side_effect=urllib.error.HTTPError("", status, "", Message(), None),
        ):
            verify_viewer_denied(None, "", "fixture")
    with patch("kaneo_private_verify.call", return_value={}):
        try:
            verify_viewer_denied(None, "", "fixture")
        except PermissionError:
            pass
        else:
            raise AssertionError("unexpected viewer access passed verification")
    print("Fictional neutral provenance, evidence, identity and viewer isolation checks passed")


if __name__ == "__main__":
    run()
