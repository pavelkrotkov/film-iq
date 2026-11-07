"""Verify fictional review imports preserve an explicitly cleared field."""

from unittest.mock import patch

import kaneo_direct_reviews as importer


def main() -> None:
    fields = [
        {"id": "identity", "name": importer.IDENTITY_FIELD, "type": "text"},
        {"id": "reviews", "name": importer.FIELD, "type": "text"},
    ]
    values = [{"taskId": "film", "fieldId": "identity", "value": "42"}]
    writes = []

    def request(_opener, _base, path, body=None, method=None):
        if path == "/custom-field/project/project":
            return fields
        if path in ("/custom-field/project/project/values", "/custom-field/task/film"):
            return values
        if path == "/task/film":
            return {"title": "Fictional film"}
        assert path == "/custom-field/value" and method == "PUT"
        assert isinstance(body, dict)
        writes.append(body)
        values.append({**body})
        return {}

    row = {"tmdb_id": 42, "links": [{"url": "https://example.invalid/review"}]}
    source = {"films": [{"tmdb_id": 42, "title": "Fictional film"}]}
    with (
        patch.object(importer, "call", request),
        patch.object(importer, "validate_review_manifests", return_value=([row], 0)),
    ):
        first = importer.import_reviews(None, "fictional", "project", {}, source, apply=True)
        assert first["written"] == 1 and len(writes) == 1
        values[-1]["value"] = ""  # API clear keeps a value row.
        preview = importer.import_reviews(None, "fictional", "project", {}, source)
        again = importer.import_reviews(None, "fictional", "project", {}, source, apply=True)
        assert preview["pending"] == 0 and preview["skipped"] == 1
        assert again["written"] == 0 and again["skipped"] == 1 and len(writes) == 1
        assert values[-1]["value"] == ""
    print("Fictional Kaneo review import preserves explicit clears")


if __name__ == "__main__":
    main()
