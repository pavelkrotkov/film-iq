"""Exercise direct-review imports with fictional records and a fake client."""

import json
from copy import deepcopy
from typing import Any
from unittest.mock import patch

import youtrack_review_import as importer
from youtrack_client import YouTrackClient, YouTrackError


class FakeClient(YouTrackClient):
    def __init__(self) -> None:
        self.records: list[dict[str, Any]] = [
            {
                "id": "1",
                "idReadable": "FILMPOC-1",
                "summary": "Fictional Film",
                "description": "Edited fictional synopsis",
                "customFields": [
                    {"name": "FilmIQ TMDB ID", "value": 123},
                    {"name": "FilmIQ Source Evidence", "value": {"text": "existing evidence"}},
                    {"name": importer.REVIEW_FIELD, "value": None},
                ],
            }
        ]
        self.writes = 0
        self.lose_response = False
        self.deny_read = False
        self.deny_write = False
        self.mismatch_read = False
        self.field_history: list[dict[str, Any]] = []

    def pages(self, path: str, *, query: dict[str, str | int]) -> list[Any]:
        if path == "issues":
            return deepcopy(self.records)
        assert path == "issues/1/activities"
        return deepcopy(self.field_history)

    def request(
        self,
        path: str,
        *,
        query: dict[str, str | int] | None = None,
        body: dict[str, Any] | None = None,
    ) -> Any:
        assert path == "issues/1"
        if body is None:
            if self.deny_read:
                raise YouTrackError("simulated denied request")
            record = deepcopy(self.records[0])
            if self.mismatch_read:
                record["customFields"][0]["value"] = 999
            return record
        assert set(body) == {"customFields"} and len(body["customFields"]) == 1
        if self.deny_write:
            raise YouTrackError("simulated denied write")
        field = body["customFields"][0]
        assert field["name"] == importer.REVIEW_FIELD
        assert self.records[0]["customFields"][2]["value"] is None
        self.records[0]["customFields"][2]["value"] = deepcopy(field["value"])
        self.writes += 1
        if self.lose_response:
            self.lose_response = False
            raise YouTrackError("simulated lost write response")
        return {}


class FakeFields(YouTrackClient):
    def __init__(self) -> None:
        self.fields: list[dict[str, Any]] = []
        self.attached: list[dict[str, Any]] = []
        self.writes = 0

    def pages(self, path: str, *, query: dict[str, str | int]) -> list[Any]:
        if path == "admin/customFieldSettings/customFields":
            return deepcopy(self.fields)
        assert path == "admin/projects/fictional-project/customFields"
        return deepcopy(self.attached)

    def request(
        self,
        path: str,
        *,
        query: dict[str, str | int] | None = None,
        body: dict[str, Any] | None = None,
    ) -> Any:
        assert body is not None
        self.writes += 1
        if path == "admin/customFieldSettings/customFields":
            self.fields.append(
                {"id": "field", "name": body["name"], "fieldType": body["fieldType"]}
            )
            return deepcopy(self.fields[-1])
        assert path == "admin/projects/fictional-project/customFields"
        assert body["$type"] == "TextProjectCustomField" and body["canBeEmpty"] is True
        self.attached.append({"id": "project-field", "field": deepcopy(body["field"])})
        return {}


def reject(action) -> None:
    try:
        action()
    except (ValueError, YouTrackError):
        return
    raise AssertionError("invalid or denied operation was accepted")


def main() -> None:
    fields = FakeFields()
    importer.ensure_review_field(fields, "fictional-project")
    assert fields.writes == 2
    importer.ensure_review_field(fields, "fictional-project")
    assert fields.writes == 2
    fields.fields[0]["fieldType"]["id"] = "integer"
    reject(lambda: importer.ensure_review_field(fields, "fictional-project"))
    assert fields.writes == 2
    source: dict[str, Any] = {
        "version": "tracker-poc-private-film-input-v1",
        "films": [
            {
                "tmdb_id": 123,
                "title": "Fictional Film",
                "director": "Fictional Director",
                "source_year": 2001,
                "origin": ["discovery"],
                "field_provenance": {"tmdb_id": "reviewed accepted identity match"},
            }
        ],
    }
    manifest: dict[str, Any] = {
        "schema_version": 1,
        "films": [
            {
                "tmdb_id": 123,
                "links": [
                    {
                        "url": "https://example.com/synthetic-review",
                        "provider": "Fictional Critic",
                        "type": "individual_critic_review",
                        "checked_at": "2026-11-05T12:00:00+00:00",
                        "identity_evidence": {
                            "input_title": "Fictional Film",
                            "source_page_title": "Fictional Film",
                            "director": "Fictional Director",
                            "input_source_year": 2001,
                            "basis": "fictional exact title and director",
                        },
                    }
                ],
            }
        ],
    }
    client = FakeClient()
    assert len(importer.combine([manifest, manifest], source)[0]["links"]) == 1
    conflicting = deepcopy(manifest)
    conflicting["films"][0]["links"][0]["provider"] = "Different fictional publisher"
    reject(lambda: importer.combine([manifest, conflicting], source))
    with (
        patch.object(importer, "project_id", return_value="fictional-project"),
        patch.object(importer, "ensure_review_field") as ensure,
    ):
        wrong_source = deepcopy(source)
        wrong_source["films"][0]["director"] = "Different director"
        reject(lambda: importer.run(client, [manifest], wrong_source, "FILMPOC"))
        duplicate = deepcopy(manifest)
        duplicate["films"].append(deepcopy(duplicate["films"][0]))
        reject(lambda: importer.run(client, [duplicate], source, "FILMPOC"))
        ensure.assert_not_called()
        client.records.append(deepcopy(client.records[0]))
        reject(lambda: importer.run(client, [manifest], source, "FILMPOC"))
        client.records.pop()
        ensure.assert_not_called()
        client.records[0]["summary"] = "User-edited title"
        assert importer.run(client, [manifest], source, "FILMPOC") == (0, 0, 1, 0)
        assert client.records[0]["summary"] == "User-edited title"
        ensure.assert_not_called()
        client.records[0]["summary"] = "Fictional Film"
        client.mismatch_read = True
        reject(lambda: importer.run(client, [manifest], source, "FILMPOC"))
        client.mismatch_read = False
        client.deny_read = True
        reject(lambda: importer.run(client, [manifest], source, "FILMPOC"))
        client.deny_read = False
        client.deny_write = True
        reject(lambda: importer.run(client, [manifest], source, "FILMPOC"))
        client.deny_write = False
        assert client.writes == 0
        before = deepcopy(client.records[0])
        client.records[0]["customFields"][2]["value"] = {"text": "user-maintained links"}
        assert importer.run(client, [manifest], source, "FILMPOC") == (0, 1, 0, 0)
        assert client.records[0]["customFields"][2]["value"]["text"] == "user-maintained links"
        client.records[0]["customFields"][2]["value"] = None
        client.field_history = [{"id": "change", "field": {"name": importer.REVIEW_FIELD}}]
        assert importer.run(client, [manifest], source, "FILMPOC") == (0, 1, 0, 0)
        assert client.writes == 0, "an explicitly cleared field must not be restored"
        client.field_history = [{"id": "malformed"}]
        reject(lambda: importer.run(client, [manifest], source, "FILMPOC"))
        assert client.writes == 0, "unreadable history must not be treated as untouched"
        client.field_history = [{"id": "other", "field": {"name": "Unrelated field"}}]
        client.lose_response = True
        reject(lambda: importer.run(client, [manifest], source, "FILMPOC"))
        assert client.writes == 1
        assert importer.run(client, [manifest], source, "FILMPOC") == (0, 1, 0, 0)
        assert client.writes == 1
        after = client.records[0]
        assert after["summary"] == before["summary"]
        assert after["description"] == before["description"]
        assert after["customFields"][:2] == before["customFields"][:2]

    watched_source: dict[str, Any] = {
        "version": "tracker-poc-private-film-input-v1",
        "films": [
            {
                "tmdb_id": 123,
                "title": "Fictional Film",
                "origin": ["movary_watched"],
                "watched": True,
                "personal_notes": "private synthetic note",
                "field_provenance": {
                    "tmdb_id": "Movary API or native export; not independently reverified here"
                },
            }
        ],
    }
    watched_manifest: dict[str, Any] = {
        "schema_version": 1,
        "films": [
            {
                "tmdb_id": 123,
                "links": [
                    {
                        "url": "https://example.com/synthetic-critic-review",
                        "provider": "Fictional Critic",
                        "type": "individual_critic_review",
                        "checked_at": "2026-11-05T12:00:00Z",
                        "identity_evidence": {
                            "input_title": "Fictional Film",
                            "source_page_title": "Fictional Film",
                            "source_directors": ["Fictional Director"],
                            "tmdb_id_source_url": "https://www.wikidata.org/wiki/Q123",
                            "basis": "Title/director checked",
                            "mapping_limit": "Source identity uncertain",
                            "personal_identity_caveat": "private synthetic caveat",
                        },
                    }
                ],
            }
        ],
    }
    watched_client = FakeClient()
    second_film = deepcopy(watched_manifest)
    second_film["films"][0]["tmdb_id"] = 124
    combined_source = {
        "version": source["version"],
        "films": [source["films"][0], {**watched_source["films"][0], "tmdb_id": 124}],
    }
    combined = importer.combine([manifest, manifest, second_film, second_film], combined_source)
    assert len(combined) == 2 and all(len(row["links"]) == 1 for row in combined)
    discovery_evidence = combined[0]["links"][0]["identity_evidence"]
    watched_evidence = combined[1]["links"][0]["identity_evidence"]
    assert set(discovery_evidence) == set(watched_evidence)
    for shared in ("identity_caveat", "details_note"):
        assert discovery_evidence[shared] == watched_evidence[shared]
    original_source = deepcopy(watched_source)
    original_manifest = deepcopy(watched_manifest)
    with (
        patch.object(importer, "project_id", return_value="fictional-project"),
        patch.object(importer, "ensure_review_field") as ensure,
    ):
        conflict = deepcopy(watched_manifest)
        conflict["films"][0]["links"][0]["identity_evidence"]["release_note"] = (
            "private synthetic note: release discrepancy"
        )
        assert importer.run(watched_client, [conflict], watched_source, "FILMPOC") == (0, 0, 0, 1)
        assert importer.run(
            watched_client, [watched_manifest, conflict], watched_source, "FILMPOC"
        ) == (0, 0, 0, 1)
        assert watched_client.writes == 0
        ensure.assert_not_called()
        assert importer.run(watched_client, [watched_manifest], watched_source, "FILMPOC") == (
            1,
            0,
            0,
            0,
        )
        assert importer.run(watched_client, [watched_manifest], watched_source, "FILMPOC") == (
            0,
            1,
            0,
            0,
        )
        saved = watched_client.records[0]["customFields"][2]["value"]["text"]
        for private_term in ("movary", "watched", "private synthetic", "personal_identity_caveat"):
            assert private_term not in saved.lower()
        evidence = json.loads(saved)["links"][0]["identity_evidence"]
        assert evidence.get("source_year") is None
        assert watched_source == original_source and watched_manifest == original_manifest
    print("Fictional YouTrack direct-review validation, preservation and retry checks passed")


if __name__ == "__main__":
    main()
