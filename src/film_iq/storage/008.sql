-- Human assertions are recorded as attestations, not verified independence.
CREATE TABLE extraction_audit (
    revision_id TEXT PRIMARY KEY REFERENCES extraction_revision(id),
    auditor TEXT NOT NULL CHECK(length(trim(auditor)) > 0),
    evidence TEXT NOT NULL CHECK(length(trim(evidence)) > 0),
    audited_at TEXT NOT NULL CHECK(length(trim(audited_at)) > 0),
    independent_attested INTEGER NOT NULL CHECK(independent_attested = 1),
    complete_attested INTEGER NOT NULL CHECK(complete_attested = 1),
    expected_count INTEGER NOT NULL CHECK(expected_count > 0),
    actual_count INTEGER NOT NULL CHECK(actual_count = expected_count),
    previous_revision_id TEXT REFERENCES extraction_revision(id)
);
