"""Fictional validation and Kaneo import checks; no external requests."""

from copy import deepcopy
from unittest.mock import patch

from direct_review_links import (
    review_manifest_conflict_count,
    validate_review_manifest,
    validate_review_manifests,
)
from kaneo_direct_reviews import import_reviews


def fixtures():
    source = {
        "version": "tracker-poc-private-film-input-v1",
        "films": [
            {
                "tmdb_id": 42,
                "title": "Fictional Title",
                "director": "Fictional Director",
                "source_year": 2001,
                "origin": ["discovery"],
                "field_provenance": {"tmdb_id": "reviewed accepted identity match"},
            }
        ],
    }
    manifest = {
        "schema_version": 1,
        "films": [
            {
                "tmdb_id": 42,
                "links": [
                    {
                        "url": "https://example.com/review",
                        "provider": "Example",
                        "type": "individual_critic_review",
                        "checked_at": "2026-11-05T12:00:00Z",
                        "identity_evidence": {
                            "input_title": "Fictional Title",
                            "source_page_title": "Fictional Title",
                            "director": "Fictional Director",
                            "input_source_year": 2001,
                            "basis": "Title and director agree",
                        },
                    }
                ],
            }
        ],
    }
    return manifest, source


def must_reject(manifest, source):
    try:
        validate_review_manifest(manifest, source)
    except ValueError:
        return
    raise AssertionError("Invalid manifest was accepted")


def run():
    manifest, source = fixtures()
    discovery_output = validate_review_manifest(manifest, source)
    assert discovery_output[0]["tmdb_id"] == 42
    for mutation in (
        "duplicate",
        "director",
        "title",
        "alternate",
        "naive_time",
        "private_url",
        "extra_prose",
        "source_unreviewed",
    ):
        candidate, ref = deepcopy(manifest), deepcopy(source)
        link = candidate["films"][0]["links"][0]
        if mutation == "duplicate":
            candidate["films"].append(deepcopy(candidate["films"][0]))
        if mutation == "director":
            link["identity_evidence"]["director"] = "Other"
        if mutation == "title":
            link["identity_evidence"]["input_title"] = "Other"
        if mutation == "alternate":
            link["identity_evidence"]["source_page_title"] = "Alternate"
        if mutation == "naive_time":
            link["checked_at"] = "2026-11-05T12:00:00"
        if mutation == "private_url":
            link["url"] = "http://127.0.0.1/review"
        if mutation == "extra_prose":
            link["review_text"] = "not allowed"
        if mutation == "source_unreviewed":
            ref["films"][0]["field_provenance"]["tmdb_id"] = "unverified"
        must_reject(candidate, ref)
    alternate = deepcopy(manifest)
    alt_evidence = alternate["films"][0]["links"][0]["identity_evidence"]
    alt_evidence.update(
        source_page_title="Alternate",
        alternate_title_basis="Source title",
        alternate_title_evidence_url="https://example.com/title",
    )
    alt_output = validate_review_manifest(alternate, source)[0]["links"][0]["identity_evidence"]
    assert alt_output["source_page_title"] == "Alternate"
    assert alt_output["corroboration_urls"] == []

    private_source = deepcopy(source)
    private_source["films"][0]["origin"] = ["movary_watched"]
    private_source["films"][0]["field_provenance"]["tmdb_id"] = (
        "Movary API or native export; not independently reverified here"
    )
    watched = deepcopy(manifest)
    watched_link = watched["films"][0]["links"][0]
    watched_link["identity_evidence"] = {
        "input_title": "Fictional Title",
        "source_page_title": "Fictional Title",
        "source_directors": ["Fictional Director"],
        "tmdb_id_source_url": "https://www.wikidata.org/wiki/Q123",
        "basis": "verified source page",
        "mapping_limit": "PRIVATE watched source limit",
        "personal_identity_caveat": "PRIVATE Movary viewing evidence",
    }
    clean = validate_review_manifest(watched, private_source)
    rendered = str(clean).casefold()
    assert all(
        term not in rendered
        for term in (
            "movary",
            "watched",
            "personal_identity_caveat",
            "mapping_limit",
            "private sensitive discrepancy",
        )
    )
    assert clean[0]["links"][0]["identity_evidence"]["source_directors"] == ["Fictional Director"]
    assert clean[0]["links"][0]["identity_evidence"]["source_year"] is None
    assert set(clean[0]["links"][0]["identity_evidence"]) == set(
        discovery_output[0]["links"][0]["identity_evidence"]
    )
    assert clean[0]["links"][0]["identity_evidence"]["corroboration_urls"] == []
    assert (
        "not independently verified" in clean[0]["links"][0]["identity_evidence"]["identity_caveat"]
    )
    conflict = deepcopy(watched)
    conflict["films"][0]["links"][0]["identity_evidence"]["release_note"] = (
        "PRIVATE sensitive discrepancy"
    )
    assert validate_review_manifest(conflict, private_source) == []
    assert review_manifest_conflict_count(conflict, private_source) == 1
    assert validate_review_manifests([watched, conflict], private_source) == ([], 1)
    for field, bad in (
        ("source_page_title", "Different"),
        ("source_directors", []),
        ("tmdb_id_source_url", "https://example.com/no-crosswalk"),
        ("source_year", "not-a-year"),
    ):
        invalid = deepcopy(watched)
        invalid["films"][0]["links"][0]["identity_evidence"][field] = bad
        must_reject(invalid, private_source)

    fields = [
        {"id": "id", "name": "POC TMDB ID", "type": "text"},
        {"id": "reviews", "name": "POC Direct Review Links", "type": "text"},
    ]
    values = [
        {"taskId": "task", "fieldId": "id", "value": "42"},
        {"taskId": "task", "fieldId": "evidence", "value": "user evidence"},
    ]
    writes = []
    record = {"title": "Fictional Title"}

    def fake(_opener, _base, path, payload=None, method=None):
        if path == "/custom-field/project/project":
            return fields
        if path == "/custom-field/project/project/values":
            return deepcopy(values)
        if path == "/task/task":
            return deepcopy(record)
        if path == "/custom-field/task/task":
            return deepcopy(values)
        if path == "/custom-field/value":
            assert method == "PUT"
            assert isinstance(payload, dict)
            writes.append(deepcopy(payload))
            values.append({**payload})
            return {"ok": True}
        raise AssertionError(path)

    with patch("kaneo_direct_reviews.call", fake):
        held = import_reviews(None, "", "project", [watched, conflict], private_source, apply=True)
        assert held["conflicts"] == 1 and held["written"] == 0 and not writes
        assert import_reviews(None, "", "project", manifest, source) == {
            "pending": 1,
            "skipped": 0,
            "conflicts": 0,
            "written": 0,
        }
        assert not writes
        assert import_reviews(None, "", "project", manifest, source, apply=True)["written"] == 1
        assert import_reviews(None, "", "project", manifest, source, apply=True)["written"] == 0
        assert len(writes) == 1 and values[1]["value"] == "user evidence"
        values[-1]["value"] = "user-edited value"
        assert import_reviews(None, "", "project", manifest, source, apply=True)["skipped"] == 1
        assert values[-1]["value"] == "user-edited value"
        values.append({"taskId": "other", "fieldId": "id", "value": "42"})
        try:
            import_reviews(None, "", "project", manifest, source, apply=True)
        except ValueError:
            pass
        else:
            raise AssertionError("duplicate tracker identity accepted")
        assert len(writes) == 1
    values.pop()
    values.pop()
    record["title"] = "User-edited title"
    with patch("kaneo_direct_reviews.call", fake):
        result = import_reviews(None, "", "project", manifest, source, apply=True)
        assert result["conflicts"] == 1 and result["written"] == 0
        assert record["title"] == "User-edited title"
    record["title"] = "Fictional Title"

    def denied(*args, **kwargs):
        if args[2] == "/custom-field/value":
            raise PermissionError("viewer denied")
        return fake(*args, **kwargs)

    with patch("kaneo_direct_reviews.call", denied):
        try:
            import_reviews(None, "", "project", manifest, source, apply=True)
        except PermissionError:
            pass
        else:
            raise AssertionError("permission failure ignored")

    def lost_after_write(*args, **kwargs):
        result = fake(*args, **kwargs)
        if args[2] == "/custom-field/value":
            raise TimeoutError("response lost")
        return result

    with patch("kaneo_direct_reviews.call", lost_after_write):
        try:
            import_reviews(None, "", "project", manifest, source, apply=True)
        except TimeoutError:
            pass
        else:
            raise AssertionError("failure ignored")
    with patch("kaneo_direct_reviews.call", fake):
        assert import_reviews(None, "", "project", manifest, source, apply=True)["written"] == 0
    print("Fictional direct-review validation, no-overwrite, permissions and retry checks passed")


if __name__ == "__main__":
    run()
