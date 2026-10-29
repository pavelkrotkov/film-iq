-- Source policy must be recorded before documents can reference a source.
CREATE TABLE source (
    id TEXT NOT NULL PRIMARY KEY, name TEXT NOT NULL, family TEXT NOT NULL,
    independence_group TEXT NOT NULL, url TEXT NOT NULL, country TEXT,
    cadence TEXT, access_policy TEXT NOT NULL CHECK(length(trim(access_policy)) > 0),
    retention_policy TEXT NOT NULL CHECK(length(trim(retention_policy)) > 0),
    redistribution_policy TEXT NOT NULL CHECK(length(trim(redistribution_policy)) > 0),
    attribution TEXT NOT NULL CHECK(length(trim(attribution)) > 0), health TEXT
);
CREATE TABLE source_run (
    id TEXT NOT NULL PRIMARY KEY, source_id TEXT NOT NULL REFERENCES source(id),
    started_at TEXT NOT NULL, finished_at TEXT, outcome TEXT NOT NULL,
    parser_version TEXT NOT NULL, error TEXT, last_success_at TEXT,
    UNIQUE(id, source_id)
);
CREATE TABLE source_document (
    id TEXT NOT NULL PRIMARY KEY, source_id TEXT NOT NULL REFERENCES source(id),
    url TEXT NOT NULL, content_hash TEXT NOT NULL, accessed_at TEXT NOT NULL,
    published_at TEXT, fetch_state TEXT NOT NULL, retention_policy TEXT NOT NULL,
    UNIQUE(source_id, url, content_hash), UNIQUE(id, source_id)
);
CREATE TABLE published_list (
    id TEXT NOT NULL PRIMARY KEY, source_id TEXT NOT NULL REFERENCES source(id),
    edition TEXT NOT NULL, author TEXT, eligibility TEXT NOT NULL,
    period TEXT, rank_semantics TEXT NOT NULL, completeness TEXT NOT NULL,
    lineage TEXT NOT NULL, UNIQUE(source_id, edition), UNIQUE(id, source_id)
);
CREATE TABLE extraction_revision (
    id TEXT NOT NULL PRIMARY KEY, source_id TEXT NOT NULL, document_id TEXT NOT NULL,
    run_id TEXT NOT NULL, extractor_version TEXT NOT NULL,
    validation_state TEXT NOT NULL, acceptance_state TEXT NOT NULL,
    FOREIGN KEY(document_id, source_id) REFERENCES source_document(id, source_id),
    FOREIGN KEY(run_id, source_id) REFERENCES source_run(id, source_id),
    UNIQUE(document_id, extractor_version), UNIQUE(id, source_id)
);
CREATE TABLE list_entry (
    id TEXT NOT NULL PRIMARY KEY, source_id TEXT NOT NULL, list_id TEXT NOT NULL,
    entry_key TEXT NOT NULL, UNIQUE(list_id, entry_key), UNIQUE(id, source_id),
    FOREIGN KEY(list_id, source_id) REFERENCES published_list(id, source_id)
);
CREATE TABLE entry_observation (
    entry_id TEXT NOT NULL, source_id TEXT NOT NULL, revision_id TEXT NOT NULL,
    raw_title TEXT NOT NULL CHECK(length(trim(raw_title)) > 0), raw_context TEXT NOT NULL,
    original_title TEXT, listed_year INTEGER, director TEXT, position INTEGER,
    rank INTEGER CHECK(rank IS NULL OR rank > 0), tie TEXT, locator TEXT NOT NULL,
    extraction_decision TEXT NOT NULL,
    PRIMARY KEY(entry_id, revision_id),
    FOREIGN KEY(entry_id, source_id) REFERENCES list_entry(id, source_id),
    FOREIGN KEY(revision_id, source_id) REFERENCES extraction_revision(id, source_id)
);
CREATE TABLE film_index (
    id INTEGER PRIMARY KEY, tmdb_id INTEGER UNIQUE, imdb_id TEXT UNIQUE, movary_id TEXT UNIQUE
);
CREATE TABLE match_decision (
    id TEXT NOT NULL PRIMARY KEY, entry_id TEXT NOT NULL, revision_id TEXT NOT NULL,
    film_id INTEGER REFERENCES film_index(id), candidates TEXT NOT NULL,
    method TEXT NOT NULL, version TEXT NOT NULL, confidence REAL,
    reviewer TEXT, decision TEXT NOT NULL, decided_at TEXT NOT NULL,
    supersedes TEXT REFERENCES match_decision(id),
    FOREIGN KEY(entry_id, revision_id) REFERENCES entry_observation(entry_id, revision_id)
);
CREATE TABLE review (
    id TEXT NOT NULL PRIMARY KEY, entry_id TEXT REFERENCES list_entry(id),
    revision_id TEXT REFERENCES extraction_revision(id), reason TEXT NOT NULL,
    status TEXT NOT NULL, created_at TEXT NOT NULL, resolution TEXT
);
