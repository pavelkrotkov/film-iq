// Synthetic CPU-only timings for the extracted YouTrack UI filter.
// Run: python3 docs/research/tracker-poc/fixture_data.py 1000 | node docs/research/tracker-poc/ui/youtrack_filter_benchmark.mjs
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import os from "node:os";
import { performance } from "node:perf_hooks";
import { filterYoutrackFilms, providerFreshness, providerObservation } from "./youtrack_filters.js";

const dataset = JSON.parse(readFileSync(0, "utf8"));
assert.equal(dataset.synthetic, true);
assert.equal(dataset.films.length, 1000);
const readable = (id) => `FILMPOC-${Number(id.slice("fixture-".length))}`;
const films = dataset.films.map((film) => ({
  id: film.fixture_id, idReadable: readable(film.fixture_id), summary: film.title,
  customFields: [
    {name:"FilmIQ Fixture ID", value:film.fixture_id},
    {name:"FilmIQ Release Year", value:film.release_year},
    {name:"FilmIQ Genre", value:film.genres[0]},
    {name:"FilmIQ Critic Score", value:film.critic_score},
    {name:"FilmIQ Critic Summary", value:{text:film.critic_summary}},
    {name:"FilmIQ Provider Observation", value:{text:JSON.stringify({source:"synthetic fixture, not TMDB", subscription:film.streaming_providers, rent:film.rental_providers, checked_at:film.availability_checked_at})}},
    {name:"FilmIQ Lifecycle", value:{name:film.lifecycle_state}},
  ],
}));
const preferences = Object.fromEntries(dataset.preferences.filter((p) => p.user_id === "user-a").map((p) => [readable(p.fixture_id), p]));
const defaults = {query:"", stateFilter:"", provider:"", genre:"", freshness:"", watchlistOnly:false, minimum:"", sortInterest:false, preferences, movaryOnly:false, excludeMovaryWatched:false, movary:null};
const scenarios = [
  {name:"All films", options:{}, expected:1000},
  {name:"Title search", options:{query:"film 01"}, expected:100},
  {name:"Netflix and interest >= 8, sorted", options:{provider:"Netflix",minimum:"8",sortInterest:true}, expected:50},
  {name:"Sort all by interest", options:{sortInterest:true}, expected:1000},
];
const unknown = {...films[0], customFields:[]};
assert.equal(providerObservation(unknown), null);
assert.equal(providerFreshness(null), "unknown");
assert.equal(filterYoutrackFilms([unknown], {...defaults,provider:"Netflix"}).length, 0);
assert.equal(filterYoutrackFilms([unknown], {...defaults,minimum:"8",preferences:null}).length, 0);
assert.equal(filterYoutrackFilms([unknown], {...defaults,excludeMovaryWatched:true,movary:null}).length, 0);
const known = {status:"available", films:{[films[0].idReadable]:{watched:true}}};
assert.equal(filterYoutrackFilms(films.slice(0,2), {...defaults,excludeMovaryWatched:true,movary:known}).length, 1);
assert.equal(filterYoutrackFilms(films.slice(0,2), {...defaults,movaryOnly:true,movary:known}).length, 1);
assert.equal(filterYoutrackFilms(films.slice(0,2), {...defaults,movaryOnly:true,movary:{...known,status:"unknown"}}).length, 0, "unknown history with stale rows must not count as watched");
assert.equal(filterYoutrackFilms(films.slice(0,2), {...defaults,excludeMovaryWatched:true,movary:{...known,status:"unknown"}}).length, 0, "unknown history cannot be used to exclude known watched films");
const warmups = 100, samples = 500;
console.log(`Node ${process.version}; ${os.platform()} ${os.arch()}; 1000 fictional films; ${warmups} warmups + ${samples} timed calls per scenario`);
for (const scenario of scenarios) {
  const options = {...defaults, ...scenario.options};
  const check = filterYoutrackFilms(films, options);
  assert.equal(check.length, scenario.expected, `${scenario.name} result count`);
  if (options.sortInterest) {
    for (let i=1; i<check.length; i++) assert.ok(preferences[check[i-1].idReadable].interest_score >= preferences[check[i].idReadable].interest_score, "interest order is numeric and descending");
  }
  if (options.provider) assert.ok(check.every((film) => providerObservation(film).subscription.includes("Netflix") && preferences[film.idReadable].interest_score >= 8));
  for (let i=0; i<warmups; i++) filterYoutrackFilms(films, options);
  const timings = [];
  for (let i=0; i<samples; i++) {
    const start = performance.now();
    filterYoutrackFilms(films, options);
    timings.push(performance.now() - start);
  }
  timings.sort((a,b) => a-b);
  const percentile = (p) => timings[Math.ceil(p * samples)-1].toFixed(3);
  console.log(`${scenario.name}: ${check.length} matches; median ${percentile(.5)} ms; p95 ${percentile(.95)} ms; max ${percentile(1)} ms`);
}
console.log("CPU-only Node measurements; excludes data loading, network, React, DOM, iframe, images and browser rendering.");
