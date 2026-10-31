-- Classification belongs to an observation revision, never a publisher name.
CREATE TABLE entry_recognition (
    entry_id TEXT NOT NULL,
    revision_id TEXT NOT NULL,
    kind TEXT NOT NULL CHECK(kind IN ('unknown','critic_selection','institutional_selection','registry_selection','award_outcome','reception_metric')),
    payload TEXT NOT NULL,
    review TEXT,
    PRIMARY KEY(entry_id,revision_id),
    FOREIGN KEY(entry_id,revision_id) REFERENCES entry_observation(entry_id,revision_id)
);
CREATE TABLE recognition_snapshot (
    id TEXT PRIMARY KEY,
    version TEXT NOT NULL,
    payload TEXT NOT NULL
);
