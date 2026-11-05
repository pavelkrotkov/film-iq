-- Local recommendation decisions are separate from Movary's personal state.
CREATE TABLE recommendation_disposition (
    tmdb_id INTEGER PRIMARY KEY REFERENCES film_index(tmdb_id),
    state TEXT NOT NULL CHECK(state IN ('saved','dismissed'))
);
