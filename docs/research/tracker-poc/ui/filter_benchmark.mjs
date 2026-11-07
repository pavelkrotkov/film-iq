// Synthetic CPU-only timings for the exact filter function used by the Kaneo UI.
// Run: python3 docs/research/tracker-poc/fixture_data.py 1000 | node docs/research/tracker-poc/ui/filter_benchmark.mjs
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import os from "node:os";
import { performance } from "node:perf_hooks";
import { filterFilms } from "./film_filters.js";

const dataset = JSON.parse(readFileSync(0, "utf8"));
assert.equal(dataset.synthetic, true);
assert.equal(dataset.films.length, 1000);
const films = dataset.films.map((film) => ({
  id: film.fixture_id, title: film.title, status: film.lifecycle_state,
  fields: {
    "POC Genre": film.genres[0],
    "POC Synthetic Availability": JSON.stringify({source:"synthetic fixture, not TMDB", subscription:film.streaming_providers, rent:film.rental_providers, checked_at:film.availability_checked_at}),
  },
}));
const preferences = Object.fromEntries(dataset.preferences.filter((p) => p.user_id === "user-a").map((p) => [p.fixture_id, p]));
const defaults = {query:"", provider:"", watchlistOnly:false, minimum:"", genre:"", lifecycle:"", watched:"", freshnessFilter:"", sortInterest:false, preferences, movaryOnly:false, excludeMovaryWatched:false, movary:null};
const scenarios = [
  {name:"All films", options:{}, expected:1000},
  {name:"Title search", options:{query:"film 01"}, expected:100},
  {name:"Netflix and interest >= 8, sorted", options:{provider:"Netflix",minimum:"8",sortInterest:true}, expected:50},
  {name:"Sort all by interest", options:{sortInterest:true}, expected:1000},
];
const warmups = 100, samples = 500;
console.log(`Node ${process.version}; ${os.platform()} ${os.arch()}; 1000 fictional films; ${warmups} warmups + ${samples} timed calls per scenario`);
for (const scenario of scenarios) {
  const options = {...defaults, ...scenario.options};
  const check = filterFilms(films, options);
  assert.equal(check.length, scenario.expected, `${scenario.name} result count`);
  if (options.sortInterest) {
    for (let i=1; i<check.length; i++) assert.ok(preferences[check[i-1].id].interest_score >= preferences[check[i].id].interest_score, "interest order is numeric and descending");
  }
  if (options.provider) assert.ok(check.every((film) => JSON.parse(film.fields["POC Synthetic Availability"]).subscription.includes("Netflix") && preferences[film.id].interest_score >= 8));
  for (let i=0; i<warmups; i++) filterFilms(films, options);
  const timings = [];
  for (let i=0; i<samples; i++) {
    const start = performance.now();
    filterFilms(films, options);
    timings.push(performance.now() - start);
  }
  timings.sort((a,b) => a-b);
  const percentile = (p) => timings[Math.ceil(p * samples)-1].toFixed(3);
  console.log(`${scenario.name}: ${check.length} matches; median ${percentile(.5)} ms; p95 ${percentile(.95)} ms; max ${percentile(1)} ms`);
}
console.log("CPU-only Node measurements; excludes data loading, network, React, DOM, images and browser rendering.");
