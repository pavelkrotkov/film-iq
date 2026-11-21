"""Exercise atomic complete-edition imports, replay and independent review binding."""

import json
import sqlite3
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

from build_catalog import Catalogue

from film_iq.discovery_command import discovery_command
from film_iq.source_library import fingerprint, publish


def check_catalogue():
    catalogue: Any = object.__new__(Catalogue)
    catalogue.resolved = {}
    catalogue.provider = SimpleNamespace(TMDbError=RuntimeError)
    calls = []

    def get(path, params):
        calls.append(params)
        return {
            "total_pages": 2,
            "total_results": 2,
            "results": [{"id": params.get("page", 1), "title": "Film", "original_title": "Film"}],
        }

    catalogue.get = get
    catalogue.movie = lambda ident: SimpleNamespace(
        tmdb_id=ident,
        title="Film",
        original_title="Film",
        year=1950,
        directors=["John Smith"],
        imdb_title_url=f"https://www.imdb.com/title/tt{ident}/",
    )
    row = {"raw_title": "Film", "director": "Smith", "year": 1950}
    _, result = catalogue.resolve(row)
    assert result["tmdb_id"] is None and len(calls) == 2
    assert calls[-1]["page"] == 2
    catalogue.get = lambda path, params: {
        "total_pages": 1,
        "total_results": 2,
        "results": [{"id": 1, "title": "Film", "original_title": "Film"}],
    }
    _, result = catalogue.resolve(row)
    assert result == {"tmdb_id": None, "reason": "ValueError"}
    calls.clear()
    catalogue.get = get
    assert len(catalogue.candidates({**row, "alternate_titles": ["Published alias"]})) == 2
    assert {call["query"] for call in calls} == {"Film", "Published alias"}


def main():
    check_catalogue()
    source: dict[str, Any] = {
        "policy": {
            "id": "fictional-list",
            "name": "Fictional annual list",
            "url": "https://example.test/films",
            "family": "critic",
            "independence_group": "fictional-editor",
            "access": "Fictional fixture",
            "retention": "Fictional fixture",
            "redistribution": "Fictional fixture",
            "attribution": "Fictional fixture",
        },
        "manifest": {
            "edition": "2025",
            "ballot_scope": "Fictional critic",
            "document_revision": "fictional-2025",
            "eligibility": "Fictional films",
            "completeness": "complete",
            "scope": "All two films",
            "lineage": "Original fictional list",
            "rank_semantics": "Published ranks",
            "rights_status": "allowed",
            "rights_evidence": "Fictional fixture",
            "permitted_use": "Test fixture",
            "expected_count": 2,
            "evidence_kind": "critic_selection",
        },
        "entries": [
            {
                "source_id": "fictional-list",
                "source_url": "https://example.test/films",
                "edition": "2025",
                "ballot_scope": "Fictional critic",
                "position": index,
                "rank": index,
                "tie": None,
                "published_at": None,
                "eligibility_date": None,
                "raw_title": f"Fictional film {index}",
                "director": None,
                "year": None,
                "tmdb_id": 100 + index if index == 1 else None,
                "identity_reviewer": "Fixture reviewer" if index == 1 else None,
                "identity_evidence": "Fictional identity evidence" if index == 1 else None,
                "locator": f"Item {index}",
            }
            for index in (1, 2)
        ],
    }
    checksum = fingerprint(source)
    bundle: dict[str, Any] = {
        "version": 1,
        "sources": [source],
        "audits": {
            checksum: {
                "source_sha256": checksum,
                "auditor": "Independent fixture reviewer",
                "evidence": "Complete fictional source checked",
                "audited_at": "2026-11-20T12:00:00+00:00",
                "independent": True,
                "complete": True,
                "expected_count": 2,
            }
        },
    }
    root = Path(__file__).resolve().parents[3]
    (root / ".cache/source-library").mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=root / ".cache/source-library") as directory:
        database, output = Path(directory) / "evidence.db", Path(directory) / "library.json"
        result = publish(bundle, database, output)
        assert result["observations"] == 2 and result["unresolved_observations"] == 1
        first = json.loads(output.read_text())
        assert first["cohorts"][0]["accepted"] == 2
        discovery = json.loads(discovery_command(output, None, database, "json"))
        assert discovery["total_candidates"] == 2 and discovery["unresolved"] == 1
        assert discovery["accepted"] == 2
        assert publish(bundle, database, output) == result
        assert json.loads(output.read_text()) == first
        changed = deepcopy(bundle)
        changed["sources"][0]["entries"][0]["rank"] = 9
        try:
            publish(changed, database, output)
        except KeyError as exc:
            assert exc.args == (fingerprint(changed["sources"][0]),)
        else:
            raise AssertionError("Changed source facts must require independent review")
        assert json.loads(output.read_text()) == first
        with patch("film_iq.source_library.private_json", side_effect=OSError("Index unavailable")):
            try:
                publish(bundle, database, output)
            except OSError as exc:
                assert str(exc) == "Index unavailable"
            else:
                raise AssertionError("Index failure must be reported")
        assert json.loads(output.read_text()) == first
        assert publish(bundle, database, output) == result
        conflicting = []
        conflicting_audits = {}
        for year in (2026, 2027):
            edition = deepcopy(source)
            edition["policy"]["id"] = "fictional-atomic"
            edition["manifest"]["edition"] = str(year)
            if year == 2027:
                edition["policy"]["name"] = "Conflicting source policy"
            for row in edition["entries"]:
                row["source_id"], row["edition"] = "fictional-atomic", str(year)
            checksum = fingerprint(edition)
            conflicting.append(edition)
            conflicting_audits[checksum] = {
                **next(iter(bundle["audits"].values())),
                "source_sha256": checksum,
            }
        try:
            publish(
                {"version": 1, "sources": conflicting, "audits": conflicting_audits},
                database,
                output,
            )
        except ValueError:
            pass
        else:
            raise AssertionError("A conflicting source policy must fail publication")
        with sqlite3.connect(database) as db:
            assert (
                db.execute("SELECT count(*) FROM source WHERE id='fictional-atomic'").fetchone()[0]
                == 0
            )
        assert json.loads(output.read_text()) == first
        award = deepcopy(source)
        award["policy"]["id"] = "fictional-award"
        award["manifest"]["evidence_kind"] = "unknown"
        for row in award["entries"]:
            row["source_id"] = "fictional-award"
        award["awards"] = [
            {
                "position": 1,
                "event": "Fictional festival",
                "edition": "2025",
                "category": "Audience award",
                "outcome": "prize",
                "recipient": "Fictional film 1",
                "recipient_kind": "film",
            }
        ]
        award_output = Path(directory) / "awards.json"
        for category in ("Audience award", "Jury award"):
            award["awards"][0]["category"] = category
            checksum = fingerprint(award)
            review = {**next(iter(bundle["audits"].values())), "source_sha256": checksum}
            publish(
                {"version": 1, "sources": [award], "audits": {checksum: review}},
                database,
                award_output,
            )
            revision = json.loads(award_output.read_text())["cohorts"][0]["revision_id"]
            if category == "Audience award":
                earlier = revision
            else:
                assert revision != earlier
    print("Complete source counts, unresolved identities, replay and review binding passed")


if __name__ == "__main__":
    main()
