"""Import independently audited source editions through the existing evidence ledger."""

import argparse
import csv
import io
import json
from contextlib import closing
from dataclasses import asdict
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path

from film_iq.ingest.accept import accept
from film_iq.ingest.audit import AuditAttestation, validate_audit
from film_iq.ingest.ballots import link_entry, record_ballot
from film_iq.ingest.curated import import_list
from film_iq.ingest.curated_csv import COLUMNS
from film_iq.ingest.curated_manifest import CuratedList
from film_iq.ingest.persist_checks import SourcePolicy, _key
from film_iq.personal_io import private_json
from film_iq.recognition.models import AwardOutcome
from film_iq.recognition.review import ClassificationReview
from film_iq.recognition.storage import classify_entry
from film_iq.storage import connect, migrate


def fingerprint(source: dict) -> str:
    """Bind independent review to the complete source facts and identity assertions."""
    body = json.dumps(source, sort_keys=True, ensure_ascii=False).encode()
    return sha256(body).hexdigest()


def source_manifest(source: dict) -> CuratedList:
    policy = SourcePolicy(**source["policy"])
    fields = dict(source["manifest"])
    if source.get("awards"):
        fields["recognition_context"] = json.dumps(
            source["awards"], sort_keys=True, ensure_ascii=False
        )
    return CuratedList(policy=policy, **fields)


def source_csv(source: dict) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=COLUMNS, extrasaction="raise")
    writer.writeheader()
    writer.writerows(source["entries"])
    return output.getvalue()


def reviewed_audit(source: dict, audit: dict) -> AuditAttestation:
    if audit.get("source_sha256") != fingerprint(source):
        raise ValueError("Source facts differ from the independently reviewed version")
    fields = {key: value for key, value in audit.items() if key != "source_sha256"}
    reviewed = AuditAttestation(**fields)
    validate_audit(reviewed)
    if reviewed.expected_count != source["manifest"]["expected_count"]:
        raise ValueError("Independent review count differs from the source edition")
    return reviewed


def import_source(source: dict, audit: dict, db, now: str) -> dict:
    manifest, body = source_manifest(source), source_csv(source)
    review = reviewed_audit(source, audit)
    # Validate the full edition before recording an acquisition or replacing evidence.
    import_list(body, manifest, accessed_at=now)
    report = import_list(body, manifest, db=db, accessed_at=now)
    revision = report["revision_id"]
    state, list_id = db.execute(
        "SELECT acceptance_state,list_id FROM extraction_revision WHERE id=?", (revision,)
    ).fetchone()
    classify_awards(db, source, review, list_id, revision)
    if state != "accepted":
        previous = db.execute(
            "SELECT revision_id FROM current_extraction WHERE list_id=?", (list_id,)
        ).fetchone()
        accept(db, revision, review, previous_revision_id=previous[0] if previous else None)
    if lineage := source.get("lineage_review"):
        record_lineage(db, source, lineage, list_id)
    report["accepted"] = report["total_candidates"]
    for row in report["candidates"]:
        row["extraction_status"] = "accepted"
    return report


def classify_awards(db, source: dict, audit: AuditAttestation, list_id: str, revision: str) -> None:
    manifest = source["manifest"]
    review = ClassificationReview(
        audit.auditor,
        audit.evidence,
        audit.audited_at,
        audit.independent,
        True,
        manifest["rights_evidence"],
        manifest["permitted_use"],
    )
    for declared in source.get("awards", []):
        fields = {key: value for key, value in declared.items() if key != "position"}
        classify_entry(
            db, _key(list_id, str(declared["position"])), revision, AwardOutcome(**fields), review
        )


def record_lineage(db, source: dict, lineage: dict, list_id: str) -> None:
    """Keep a named critic shared across publishers and aggregates explicitly separate."""
    kind = lineage["kind"]
    if kind not in {"original", "derivative"} or not lineage.get("evidence"):
        raise ValueError("Reviewed original or derivative lineage is required")
    db.execute(
        "UPDATE published_list SET lineage_kind=?,lineage_verification='verified' WHERE id=?",
        (kind, list_id),
    )
    contributor = lineage.get("contributor_id")
    if contributor is None:
        return
    db.execute(
        "UPDATE source SET independence_verification='verified' WHERE id=?",
        (source["policy"]["id"],),
    )
    ballot_id = _key(list_id, "original-ballot")
    record_ballot(
        db,
        ballot_id,
        list_id,
        source["manifest"]["ballot_scope"],
        contributor_id=contributor,
        contributor_name=lineage["contributor_name"],
    )
    for row in source["entries"]:
        link_entry(db, _key(list_id, str(row["position"])), ballot_id)


def publish(bundle: dict, database: Path, output: Path) -> dict:
    """Commit audited editions together, then atomically replace the discovery index."""
    if bundle.get("version") != 1 or not bundle.get("sources"):
        raise ValueError("A nonempty version-one source bundle is required")
    sources = bundle["sources"]
    identities = [(source["policy"]["id"], source["manifest"]["edition"]) for source in sources]
    if len(identities) != len(set(identities)):
        raise ValueError("Supply each source edition once")
    # Preflight every count, rank, identity, rights assertion and audit before writing.
    for source in sources:
        reviewed_audit(source, bundle["audits"][fingerprint(source)])
        import_list(source_csv(source), source_manifest(source), accessed_at="preflight")
    now = datetime.now(UTC).isoformat()
    with closing(connect(database)) as db:
        migrate(db)
        with db:
            db.execute("BEGIN")
            reports = [
                import_source(source, bundle["audits"][fingerprint(source)], db, now)
                for source in sources
            ]
    # A failed index write is retried with this bundle and reuses semantic revisions.
    private_json(output, {"version": 1, "sources": sources, "cohorts": reports})
    unique = {
        row["tmdb_id"] for report in reports for row in report["candidates"] if row["tmdb_id"]
    }
    return {
        "source_editions": len(reports),
        "observations": sum(report["total_candidates"] for report in reports),
        "reviewed_films": len(unique),
        "unresolved_observations": sum(report["unresolved"] for report in reports),
        "coverage": [
            {
                **asdict(source_manifest(source).policy),
                "edition": source["manifest"]["edition"],
                "completeness": report["completeness"],
                "expected_count": source["manifest"]["expected_count"],
                "observed_count": report["total_candidates"],
                "unresolved": report["unresolved"],
            }
            for source, report in zip(sources, reports, strict=True)
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(publish(json.loads(args.bundle.read_text()), args.database, args.output)))


if __name__ == "__main__":
    main()
