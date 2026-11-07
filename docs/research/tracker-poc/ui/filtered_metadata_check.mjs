import assert from "node:assert/strict";
import { filterFilms } from "./film_filters.js";
import { chooseRemaining, expireCachedResults, runRemainingBatch } from "./live_batch.js";
import { matchedLive } from "./kaneo_identity.js";
import { filterYoutrackFilms } from "./youtrack_filters.js";
import { attachMatchedLive, mergeLiveResult, remainingLiveFilms, runRemainingLive, titleNeedsReview } from "./youtrack_tmdb.js";
import { filterMayExcludeUnknown } from "./metadata_filter_coverage.js";

assert.equal(filterMayExcludeUnknown({freshness: "recent"}), true);
assert.equal(filterMayExcludeUnknown({freshness: "stale"}), true);
assert.equal(filterMayExcludeUnknown({freshness: "unknown"}), false);
assert.equal(filterMayExcludeUnknown({freshness: "unknown", provider: "Netflix"}), true);
assert.equal(filterMayExcludeUnknown({genre: "Drama"}), true);

// The first film is known to match; a second matching film is hidden because
// its data has not been loaded. The third is archived and is loaded only by
// the explicit all-project action, remaining hidden until archives are shown.
const live = (id) => ({tmdb_id: id, title: `Fictional ${id}`, genres: ["Drama"], availability: {status: "complete", checked_at: "2000-01-01T00:00:00Z", offers: [{kind: "subscription", provider: "Netflix"}]}});
const kaneo = [1, 2, 3].map((id) => ({id: String(id), title: `Fictional ${id}`, status: id === 3 ? "archived" : "to-do", fields: {"POC TMDB ID": String(id)}}));
const kaneoResults = {"1": {data: live(1), requestedId: 1}};
const kOptions = {query: "", provider: "Netflix", genre: "Drama", preferences: {}};
const kShown = () => kaneo.map((film) => ({...film, live: matchedLive(film, kaneoResults[film.id])}));
assert.deepEqual(filterFilms(kShown(), kOptions).map((film) => film.id), ["1"]);
assert.deepEqual(filterFilms(kShown(), {...kOptions, provider: "", genre: "", freshnessFilter: "stale"}).map((film) => film.id), ["1"]);
assert.deepEqual(filterFilms(kShown(), {...kOptions, provider: "", genre: "", freshnessFilter: "unknown"}).map((film) => film.id), ["2"]);
assert.equal(chooseRemaining(filterFilms(kShown(), kOptions), kaneoResults).length, 0);
const kRemaining = chooseRemaining(kaneo, kaneoResults);
assert.deepEqual(kRemaining.map((film) => film.id), ["2", "3"]);
const requested = [];
await runRemainingBatch(kRemaining, async (id) => {requested.push(id); return live(id);}, new AbortController().signal,
  (id, result) => {kaneoResults[id] = result;});
assert.deepEqual(requested, [2, 3]);
assert.deepEqual(filterFilms(kShown(), kOptions).map((film) => film.id), ["1", "2"]);
assert.deepEqual(filterFilms(kShown(), {...kOptions, showArchived: true}).map((film) => film.id), ["1", "2", "3"]);

// An unknown live result must not silently promote an older fixture field to
// current availability or freshness. A retained complete result, however,
// remains searchable when an incomplete refresh leaves it in the cache.
const oldFixture = JSON.stringify({source: "synthetic fixture, not TMDB", subscription: ["Netflix"], rent: [], checked_at: "2000-01-01T00:00:00Z"});
const unknownKaneo = {...kaneo[0], fields: {...kaneo[0].fields, "POC Synthetic Availability": oldFixture}, live: {...live(1), availability: {status: "unknown", checked_at: "2026-11-05T00:00:00Z", offers: []}}};
assert.deepEqual(filterFilms([unknownKaneo], {...kOptions, genre: ""}), [], "unknown live availability must not match stored providers");
assert.deepEqual(filterFilms([unknownKaneo], {...kOptions, provider: "", genre: "", freshnessFilter: "unknown"}).map((film) => film.id), ["1"], "unknown live availability stays unknown for freshness");
assert.deepEqual(filterFilms([{...unknownKaneo, live: live(1)}], {...kOptions, genre: ""}).map((film) => film.id), ["1"], "retained complete availability remains searchable");

const yt = [1, 2, 3].map((id) => ({id: `internal-${id}`, idReadable: `FILMPOC-${id}`, summary: `Fictional ${id}`, customFields: [
  {name: "FilmIQ TMDB ID", value: id}, {name: "FilmIQ Lifecycle", value: {name: id === 3 ? "Archived" : "Discovery"}},
]}));
const ytResults = {"FILMPOC-1": {data: live(1), requestedId: 1}};
const yOptions = {query: "", provider: "Netflix", genre: "Drama", preferences: {}};
const yShown = () => attachMatchedLive(yt, ytResults);
// Cache retention removes expired observations rather than making them stale.
const expired = {...live(1), cache_expires_at:"2000-01-08T00:00:00Z"};
const expiredK = expireCachedResults({"1":{data:expired,requestedId:1}}).results;
const expiredY = expireCachedResults({"FILMPOC-1":{data:expired,requestedId:1}}).results;
const kAfterExpiry = [{...kaneo[0],live:matchedLive(kaneo[0],expiredK["1"])}];
const yAfterExpiry = attachMatchedLive([yt[0]],expiredY);
assert.equal(filterFilms(kAfterExpiry,{freshnessFilter:"stale"}).length,0);
assert.equal(filterFilms(kAfterExpiry,{freshnessFilter:"unknown"}).length,1);
assert.equal(filterYoutrackFilms(yAfterExpiry,{freshness:"stale"}).length,0);
assert.equal(filterYoutrackFilms(yAfterExpiry,{freshness:"unknown"}).length,1);
assert.deepEqual(filterYoutrackFilms(yShown(), yOptions).map((film) => film.idReadable), ["FILMPOC-1"]);
assert.deepEqual(filterYoutrackFilms(yShown(), {...yOptions, provider: "", genre: "", freshness: "stale"}).map((film) => film.idReadable), ["FILMPOC-1"]);
assert.deepEqual(filterYoutrackFilms(yShown(), {...yOptions, provider: "", genre: "", freshness: "unknown"}).map((film) => film.idReadable), ["FILMPOC-2"]);
assert.equal(remainingLiveFilms(filterYoutrackFilms(yShown(), yOptions), ytResults).length, 0);
const yRemaining = remainingLiveFilms(yt, ytResults);
assert.deepEqual(yRemaining.map((film) => film.idReadable), ["FILMPOC-2", "FILMPOC-3"]);
const yRequested = [];
await runRemainingLive({fetchYouTrack: async (path) => {
  const id = Number(path.match(/FILMPOC-(\d+)/)[1]);
  yRequested.push(id);
  return live(id);
}}, yRemaining, () => true, (film, result) => {ytResults[film.idReadable] = mergeLiveResult(ytResults[film.idReadable], result);});
assert.deepEqual(yRequested, [2, 3]);
assert.deepEqual(filterYoutrackFilms(yShown(), yOptions).map((film) => film.idReadable), ["FILMPOC-1", "FILMPOC-2"]);
assert.deepEqual(filterYoutrackFilms(yShown(), {...yOptions, showArchived: true}).map((film) => film.idReadable), ["FILMPOC-1", "FILMPOC-2", "FILMPOC-3"]);

// Only an actual response for this film can flag a title difference; missing
// metadata and the exact original title remain distinct from a mismatch.
const different = {...live(1), title: "Another fictional title", original_title: "Original fictional title"};
assert.equal(titleNeedsReview(1, "Fictional 1", different), true);
assert.equal(titleNeedsReview(2, "Fictional 1", different), false);
assert.equal(titleNeedsReview(1, "Fictional 1", null), false);
assert.equal(titleNeedsReview(1, "", different), false);
assert.equal(titleNeedsReview(1, "Original fictional title", different), false);
const kReview = [{...kaneo[0], titleNeedsReview: titleNeedsReview(1, kaneo[0].title, different)}, kaneo[1]];
assert.deepEqual(filterFilms(kReview, {query: "", titleReviewOnly: true}).map((film) => film.id), ["1"]);
const yReview = attachMatchedLive(yt, {"FILMPOC-1": {data: different}});
assert.deepEqual(filterYoutrackFilms(yReview, {query: "", titleReviewOnly: true}).map((film) => film.idReadable), ["FILMPOC-1"]);
assert.equal(yReview[0].live, undefined, "mismatched artwork and providers remain withheld");
console.log("Filtered unknown metadata and explicit project-wide fictional lookup passed for both UIs");
