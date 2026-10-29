-- Verification and classification are separate facts; never infer either from prose.
ALTER TABLE published_list ADD COLUMN lineage_kind TEXT NOT NULL DEFAULT 'unknown'
    CHECK(lineage_kind IN ('unknown', 'original', 'derivative'));
