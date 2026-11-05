"""Synthetic interleaved-edit check; no service requests."""

from copy import deepcopy
from unittest.mock import patch

from kaneo_private_import import PUBLIC_IDENTITY_PROVENANCE
from kaneo_private_import_check import synthetic_manifest
from kaneo_provenance_migration import _legacy, migrate


def run() -> None:
    source = synthetic_manifest()
    source["films"] = source["films"][:1]
    before_source = deepcopy(source)
    old = _legacy(source["films"][0])
    values = {"id": str(source["films"][0]["tmdb_id"]), "p1": old[0], "p2": old[1]}
    definitions = [
        {"id": "id", "name": "POC TMDB ID", "type": "text"},
        {"id": "p1", "name": "POC Identity Provenance", "type": "text"},
        {"id": "p2", "name": "POC Field Provenance", "type": "text"},
    ]
    task_reads = 0
    writes = []

    def fake(_opener, _base, path, payload=None, method=None):
        nonlocal task_reads
        if path == "/custom-field/project/project":
            return definitions
        if path == "/custom-field/project/project/values":
            return [
                {"taskId": "task", "fieldId": field, "value": value}
                for field, value in values.items()
            ]
        if path == "/custom-field/task/task":
            task_reads += 1
            if task_reads == 4:
                values["p2"] = "User edit during migration"
            return [
                {"taskId": "task", "fieldId": field, "value": value}
                for field, value in values.items()
            ]
        if path == "/custom-field/value":
            assert method == "PUT" and isinstance(payload, dict)
            values[payload["fieldId"]] = payload["value"]
            writes.append(payload["fieldId"])
            return {}
        raise AssertionError(path)

    with patch("kaneo_provenance_migration.call", fake):
        result = migrate(None, "", "project", source, apply=True)
    assert result == {"pending": 0, "already": 0, "conflicts": 1, "updated": 0}
    assert writes == ["p1"] and values["p1"] == PUBLIC_IDENTITY_PROVENANCE
    assert values["p2"] == "User edit during migration" and source == before_source
    print("Synthetic intervening edit was preserved and reported as a conflict")


if __name__ == "__main__":
    run()
