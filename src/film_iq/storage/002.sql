-- Source-provided identifiers are raw evidence, not resolved film identities.
ALTER TABLE entry_observation ADD COLUMN raw_imdb_id TEXT;
ALTER TABLE entry_observation ADD COLUMN raw_tmdb_id TEXT;
