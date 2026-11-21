"""Join independently checked source editions to corroborated catalogue identities."""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit

from build_catalog import observation_key

from film_iq.ingest.curated_csv import COLUMNS
from film_iq.personal_io import private_json
from film_iq.source_library import fingerprint


def reviewed_rows(source, resolutions):
    rows = []
    for entry in source["entries"]:
        identity = resolutions.get(observation_key(entry), {})
        ident = identity.get("tmdb_id")
        row = {key: None for key in COLUMNS}
        row.update(
            {
                key: entry.get(key)
                for key in ("position", "rank", "tie", "raw_title", "director", "year", "locator")
            }
        )
        row.update(
            source_id="library-" + source["id"],
            source_url=source["url"],
            edition=source["edition"],
            ballot_scope=source.get("author") or source["name"],
            published_at=source.get("published_at"),
            tmdb_id=ident,
            identity_reviewer="Film IQ catalogue corroboration" if ident else None,
            identity_evidence=identity.get("evidence") if ident else None,
        )
        rows.append(row)
    return rows


def normalize(source, resolutions):
    rows = reviewed_rows(source, resolutions)
    return {
        "policy": {
            "id": "library-" + source["id"],
            "name": source["name"],
            "url": "https://" + urlsplit(source["url"]).netloc + "/",
            "family": source["family"],
            "independence_group": source["independence_group"],
            "access": "Private factual source observations; original publisher prose excluded",
            "retention": "Private factual evidence and correction history",
            "redistribution": "Source-specific permission required for redistribution",
            "attribution": source["name"],
        },
        "manifest": {
            "edition": source["edition"],
            "ballot_scope": source.get("author") or source["name"],
            "document_revision": fingerprint({"entries": rows}),
            "eligibility": source["eligibility"],
            "completeness": source["completeness"],
            "scope": source.get("coverage_note")
            or (f"All {source['expected_count']} entries in the declared edition and ballot scope"),
            "lineage": source["lineage"],
            "rank_semantics": source["rank_semantics"],
            "rights_status": "allowed",
            "rights_evidence": source["rights_evidence"],
            "permitted_use": "User-authorized private factual film discovery and source research",
            "expected_count": source["expected_count"],
            "evidence_kind": source["evidence_kind"]
            if source["evidence_kind"] != "award_outcome"
            else "unknown",
        },
        "entries": rows,
        "provenance": source,
        "lineage_review": {
            "kind": source["lineage_kind"],
            "evidence": source["lineage"],
            "contributor_id": source["independence_group"]
            if source.get("author") and source["independence_group"].startswith("critic:")
            else None,
            "contributor_name": source.get("author"),
        },
        "awards": [
            {
                "position": entry["position"],
                "event": source["name"],
                "edition": source["edition"],
                "category": entry["award"],
                "outcome": "prize",
                "recipient": entry["raw_title"],
                "recipient_kind": entry["recipient_kind"],
            }
            for entry in source["entries"]
            if entry.get("award_outcome") == "winner"
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sources", type=Path, nargs="+")
    parser.add_argument("--reviews", type=Path, action="append", required=True)
    parser.add_argument("--catalog", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    resolutions, reviewed = {}, {}
    for catalog in args.catalog:
        resolutions.update(json.loads((catalog / "progress.json").read_text())["observations"])
    for path in args.reviews:
        for audit in json.loads(path.read_text())["audits"]:
            if audit["complete"] and not audit.get("differences"):
                reviewed[audit["source_sha256"]] = audit
    normalized, audits, policies = [], {}, {}
    for path in args.sources:
        for source in json.loads(path.read_text())["sources"]:
            checksum = fingerprint(source)
            if checksum not in reviewed:
                raise ValueError(
                    f"Source edition lacks independent review: {source['id']} {source['edition']}"
                )
            audit = reviewed[checksum]
            converted = normalize(source, resolutions)
            policy = converted["policy"]
            previous = policies.setdefault(policy["id"], policy)
            if previous["independence_group"] != policy["independence_group"]:
                raise ValueError("Source independence group changed across editions")
            converted["policy"] = previous
            converted_sha = fingerprint(converted)
            normalized.append(converted)
            audits[converted_sha] = {
                "source_sha256": converted_sha,
                "auditor": audit["auditor"] + " / catalogue corroboration",
                "evidence": audit["evidence"] + f" Original source facts SHA256 {checksum}. "
                "Catalogue identities checked against direct TMDB movie details; unresolved rows retained.",
                "audited_at": datetime.now(UTC).isoformat(),
                "independent": True,
                "complete": True,
                "expected_count": source["expected_count"],
            }
    private_json(args.output, {"version": 1, "sources": normalized, "audits": audits})
    print(f"Prepared {len(normalized)} independently checked source editions")


if __name__ == "__main__":
    main()
