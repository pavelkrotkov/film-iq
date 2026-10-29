-- Existing labels are descriptive, not proof of independence or lineage.
ALTER TABLE source ADD COLUMN independence_verification TEXT NOT NULL DEFAULT 'unknown'
    CHECK(independence_verification IN ('unknown', 'verified', 'disputed'));
ALTER TABLE published_list ADD COLUMN lineage_verification TEXT NOT NULL DEFAULT 'unknown'
    CHECK(lineage_verification IN ('unknown', 'verified', 'disputed'));

-- A current match must point to the accepted decision for this observation and film.
CREATE UNIQUE INDEX match_decision_current_key
    ON match_decision(id, entry_id, revision_id, film_id, decision);
CREATE TABLE current_match (
    entry_id TEXT NOT NULL, revision_id TEXT NOT NULL,
    decision_id TEXT NOT NULL, film_id INTEGER NOT NULL,
    decision TEXT NOT NULL DEFAULT 'accepted' CHECK(decision = 'accepted'),
    PRIMARY KEY(entry_id, revision_id),
    FOREIGN KEY(decision_id, entry_id, revision_id, film_id, decision)
        REFERENCES match_decision(id, entry_id, revision_id, film_id, decision)
);
