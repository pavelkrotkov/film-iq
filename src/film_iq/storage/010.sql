-- Permitted provider observations remain separate from editorial extractions.
CREATE TABLE offer_policy (
    source TEXT PRIMARY KEY,
    payload TEXT NOT NULL,
    reviewed_at TEXT NOT NULL
);
CREATE TABLE offer_fetch (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL REFERENCES offer_policy(source),
    scope TEXT NOT NULL,
    checked_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    policy_payload TEXT NOT NULL,
    payload TEXT NOT NULL
);
CREATE INDEX offer_fetch_scope ON offer_fetch(scope,checked_at);
CREATE TABLE offer_current (
    scope TEXT PRIMARY KEY,
    fetch_id TEXT NOT NULL REFERENCES offer_fetch(id) ON DELETE CASCADE
);
CREATE TABLE offer_event (
    id TEXT PRIMARY KEY,
    fetch_id TEXT NOT NULL REFERENCES offer_fetch(id) ON DELETE CASCADE,
    payload TEXT NOT NULL
);
