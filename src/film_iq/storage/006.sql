-- Adapter-specific provenance remains attached to its extraction revision.
CREATE TABLE extraction_detail (
    revision_id TEXT PRIMARY KEY REFERENCES extraction_revision(id),
    document_revision TEXT NOT NULL, original_url TEXT NOT NULL,
    extraction_scope TEXT NOT NULL, review_reason TEXT NOT NULL
);
