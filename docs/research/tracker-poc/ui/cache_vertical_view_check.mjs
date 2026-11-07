// Test-only projection of fictional cached observations into existing filters.
import assert from "node:assert/strict";
import {filterFilms, providers} from "./film_filters.js";
import {filterYoutrackFilms, providerObservation} from "./youtrack_filters.js";

let input = "";
for await (const chunk of process.stdin) input += chunk;
const views = JSON.parse(input);
assert.equal(views.length, 2);
assert.ok(Number.isInteger(views[0].tmdb_id) && views[0].tmdb_id > 0);
assert.equal(views[0].tmdb_id, views[1].tmdb_id);
for (const live of views) {
  assert.equal(live.title, `Synthetic imported film ${live.tmdb_id}`);
  assert.equal(live.availability.status, "complete");
  assert.equal(live.availability.checked_at, "2026-01-01T00:00:00+00:00");
}
const kaneo = {id: "fictional-kaneo", title: views[0].title, status: "to-do", fields: {}, live: views[0]};
const youtrack = {id: "fictional-youtrack", idReadable: "FILMPOC-1", summary: views[1].title, customFields: [], live: views[1]};
assert.deepEqual(providers(kaneo), ["Fixture Stream"]);
assert.deepEqual(providerObservation(youtrack).subscription, ["Fixture Stream"]);
assert.equal(filterFilms([kaneo], {query: "", provider: "Fixture Stream"}).length, 1);
assert.equal(filterYoutrackFilms([youtrack], {query: "", provider: "Fixture Stream"}).length, 1);
assert.equal(filterFilms([kaneo], {query: "", provider: "Not present"}).length, 0);
assert.equal(filterYoutrackFilms([youtrack], {query: "", provider: "Not present"}).length, 0);
console.log("Fictional cache view filters passed");
