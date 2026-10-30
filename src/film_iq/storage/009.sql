-- Operational fetch attempts do not replace semantic source_run identities.
CREATE TABLE acquisition_permission (
    source_id TEXT PRIMARY KEY REFERENCES source(id),
    method TEXT NOT NULL CHECK(length(trim(method)) > 0),
    decision TEXT NOT NULL CHECK(decision IN ('allowed','blocked')),
    evidence TEXT NOT NULL CHECK(length(trim(evidence)) > 0),
    reviewed_at TEXT NOT NULL,
    retain_until TEXT
);
CREATE TABLE acquisition_attempt (
    id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES acquisition_permission(source_id),
    started_at TEXT NOT NULL,
    finished_at TEXT,
    outcome TEXT NOT NULL CHECK(outcome IN ('running','success','partial','error','unknown')),
    previous_cursor TEXT,
    permission_snapshot TEXT NOT NULL,
    cursor TEXT,
    revision_id TEXT REFERENCES extraction_revision(id),
    error_code TEXT,
    CHECK((outcome = 'running') = (finished_at IS NULL)),
    CHECK(outcome = 'success' OR (cursor IS NULL AND revision_id IS NULL)),
    CHECK(outcome != 'success' OR revision_id IS NOT NULL)
);
CREATE TABLE acquisition_cursor (
    source_id TEXT PRIMARY KEY REFERENCES source(id),
    attempt_id TEXT NOT NULL UNIQUE REFERENCES acquisition_attempt(id),
    cursor TEXT,
    succeeded_at TEXT NOT NULL
);
CREATE UNIQUE INDEX list_entry_ballot_key ON list_entry(id,list_id);
-- A contributor key is an explicit reviewed identity, never a publisher grouping.
CREATE TABLE source_ballot (
    id TEXT PRIMARY KEY,
    list_id TEXT NOT NULL REFERENCES published_list(id),
    scope TEXT NOT NULL CHECK(length(trim(scope)) > 0),
    contributor_id TEXT,
    contributor_name TEXT,
    original_ballot_id TEXT REFERENCES source_ballot(id),
    published_at TEXT,
    UNIQUE(id,list_id),
    CHECK(contributor_id IS NULL OR length(trim(contributor_id)) > 0)
);
CREATE TABLE entry_ballot (
    entry_id TEXT PRIMARY KEY,
    list_id TEXT NOT NULL,
    ballot_id TEXT NOT NULL,
    FOREIGN KEY(entry_id,list_id) REFERENCES list_entry(id,list_id),
    FOREIGN KEY(ballot_id,list_id) REFERENCES source_ballot(id,list_id)
);
