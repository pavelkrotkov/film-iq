-- Digest the complete adapter output, including fields not represented in observations.
CREATE TABLE extraction_fingerprint (
    revision_id TEXT PRIMARY KEY REFERENCES extraction_revision(id),
    output_sha256 TEXT NOT NULL
);
