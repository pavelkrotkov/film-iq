import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { filterFilms, freshness } from "./film_filters.js";

const dataset = JSON.parse(readFileSync(0, "utf8"));
assert.equal(dataset.films.length, 30);
const films = dataset.films.map((film) => ({
  id: film.fixture_id,
  title: film.title,
  status: film.lifecycle_state,
  fields: {
    "POC Genre": film.genres[0],
    "POC Subscription Providers": JSON.stringify(film.streaming_providers),
  },
}));
const preferences = (user) =>
  Object.fromEntries(
    dataset.preferences
      .filter((p) => p.user_id === user)
      .map((p) => [p.fixture_id, p]),
  );
const options = {
  query: "",
  provider: "Netflix",
  watchlistOnly: false,
  minimum: "8",
  genre: "",
  lifecycle: "",
  watched: "",
  freshnessFilter: "",
  sortInterest: true,
  preferences: preferences("user-a"),
};
assert.deepEqual(
  filterFilms(films, options)
    .map((f) => f.id)
    .sort(),
  ["fixture-0008", "fixture-0028"],
);
assert.deepEqual(
  filterFilms(films, { ...options, preferences: preferences("user-b") })
    .map((f) => f.id)
    .sort(),
  ["fixture-0004", "fixture-0016", "fixture-0024"],
);
const ordered = filterFilms(films, { ...options, provider: "", minimum: "" });
assert.equal(options.preferences[ordered[0].id].interest_score, 10);
assert.ok(
  ordered.findIndex((f) => options.preferences[f.id].interest_score === 9) >
    ordered.findIndex((f) => options.preferences[f.id].interest_score === 10),
);
assert.equal(freshness(films[0]), "unknown");
assert.equal(
  filterFilms(films, {
    ...options,
    provider: "",
    minimum: "",
    watched: "unmarked",
    preferences: null,
  }).length,
  0,
);
const withoutPreference = { ...options.preferences };
delete withoutPreference[films[0].id];
assert.ok(
  !filterFilms(films, {
    ...options,
    provider: "",
    minimum: "",
    watched: "unmarked",
    preferences: withoutPreference,
  }).some((film) => film.id === films[0].id),
  "a missing preference is not evidence that the film is unwatched",
);
const fresh = {
  fields: {
    "POC Synthetic Availability": JSON.stringify({
      source: "synthetic fixture, not TMDB",
      subscription: [],
      rent: [],
      checked_at: "2026-11-05T00:00:00Z",
    }),
  },
};
assert.equal(freshness(fresh, Date.parse("2026-11-06T00:00:00Z")), "recent");
assert.equal(freshness(fresh, Date.parse("2026-11-20T00:00:00Z")), "stale");
const live = {
  id: "live", title: "Fixture", status: "to-do", fields: {},
  live: {genres: ["Drama"], availability: {
    status: "partial", checked_at: "2026-11-05T00:00:00Z",
    offers: [{provider: "Fixture Stream", kind: "subscription"}, {provider: "Rental", kind: "rent"}],
  }},
};
assert.deepEqual(filterFilms([live], {...options, provider: "Fixture Stream", minimum: "", genre: "Drama"}).map((film) => film.id), ["live"]);
assert.equal(freshness(live, Date.parse("2026-11-06T00:00:00Z")), "recent");
const movaryFilm = { ...live, fields: {"POC TMDB ID": "12"} };
assert.equal(filterFilms([movaryFilm], { ...options, provider: "", minimum: "", movaryOnly: true, movary: {status: "available", films: {"12": {watched: true}}} }).length, 1);
assert.equal(filterFilms([movaryFilm], { ...options, provider: "", minimum: "", movaryOnly: true, movary: {status: "unknown", films: {"12": {watched: true}}} }).length, 0, "unknown history must not supply watched matches");
assert.equal(filterFilms([movaryFilm], { ...options, provider: "", minimum: "", movaryOnly: true, movary: null }).length, 0);
const otherFilm = { ...live, id: "other", fields: {"POC TMDB ID": "13"} };
const byMovary = { ...options, provider: "", minimum: "", excludeMovaryWatched: true };
const userAHistory = {status: "available", films: {"12": {watched: true}}};
const userBHistory = {status: "available", films: {"13": {watched: true}}};
assert.deepEqual(filterFilms([movaryFilm, otherFilm], {...byMovary, movary: userAHistory}).map((film) => film.id), ["other"], "exclude only user A's known watched film; unknown remains visible");
assert.deepEqual(filterFilms([movaryFilm, otherFilm], {...byMovary, movary: userBHistory}).map((film) => film.id), ["live"], "another user has an independent watched history");
assert.equal(filterFilms([movaryFilm], {...byMovary, movary: null}).length, 0, "unavailable history must not silently act as an empty history");
console.log(
  "30-fixture user-specific provider filter, numeric sort and freshness checks passed",
);
