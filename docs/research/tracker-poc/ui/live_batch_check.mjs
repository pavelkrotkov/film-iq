import assert from "node:assert/strict";
import { BATCH_LIMIT, chooseBatch, chooseRemaining, fetchLiveMovie, mergeResult, preserveEarlierPoster, refreshNotice, RateLimitError, runBatch, runRemainingBatch, safeImdbTitleUrl } from "./live_batch.js";

const films = Array.from({length: 35}, (_, index) => ({
  id: `task-${index}`,
  fields: {"POC TMDB ID": String(index + 1)},
}));
assert.equal(safeImdbTitleUrl("https://www.imdb.com/title/tt0000042/"), "https://www.imdb.com/title/tt0000042/");
assert.equal(safeImdbTitleUrl("https://www.imdb.com.evil.example/title/tt0000042/"), null);
assert.equal(safeImdbTitleUrl("https://www.imdb.com/title/tt0000042/other"), null);
films.push({id: "bad", fields: {"POC TMDB ID": "not-an-id"}});
const chosen = chooseBatch(films, {});
assert.equal(chosen.length, BATCH_LIMIT);
const controller = new AbortController();
const events = [];
const outcome = await runBatch(chosen, async (id) => {
  if (id === 2) throw new Error("fixture failure");
  if (id === 3) controller.abort();
  return {tmdb_id: id};
}, controller.signal, (id, result) => events.push([id, result]));
assert.deepEqual(outcome, {succeeded: 1, failed: 1, cancelled: true, rateLimited: false});
assert.equal(events.length, 2);
assert.ok(events[1][1].error);
assert.equal(chooseBatch(films, {"task-0": {data: {tmdb_id: 1}}, "task-1": {requestedId: 2, error: "failed"}})[0].id, "task-2");
assert.deepEqual(chooseBatch(films, {"task-1": {requestedId: 2, error: "failed"}}, true).map((film) => film.id), ["task-1"]);
const prior = {data: {tmdb_id: 2, availability: {status: "complete", offers: ["fixture"]}}};
const oldPoster = {tmdb_id:2,title:"Fictional",poster_url:"https://image.tmdb.org/t/p/w500/fictional.jpg",availability:{status:"complete",checked_at:"2026-01-01T00:00:00Z",offers:[]}};
const missingPoster = {tmdb_id:2,title:"Fictional",poster_url:null,availability:{status:"complete",checked_at:"2026-01-02T00:00:00Z",offers:[]}};
const retainedPoster = mergeResult({data:oldPoster}, {data:missingPoster}).data;
assert.equal(retainedPoster.poster_url, oldPoster.poster_url);
assert.equal(retainedPoster.poster_from_previous, true, "retained artwork must be labeled earlier");
assert.equal(retainedPoster.availability.checked_at, missingPoster.availability.checked_at, "provider freshness stays independent");
assert.equal(preserveEarlierPoster(null, missingPoster).poster_url, null, "no previous poster remains unknown");
assert.equal(preserveEarlierPoster(oldPoster, {...missingPoster,tmdb_id:3}).poster_url, null, "different ID must not inherit artwork");
assert.equal(preserveEarlierPoster(oldPoster, {...missingPoster,title:"Different"}).poster_url, null, "different title must not inherit artwork");
const replacement = {...missingPoster,poster_url:"https://image.tmdb.org/t/p/w500/new.jpg"};
assert.equal(preserveEarlierPoster(retainedPoster, replacement).poster_from_previous, undefined, "fresh artwork clears the earlier label");
const preserved = mergeResult(prior, {data: {tmdb_id: 2, availability: {status: "unknown", offers: []}}});
assert.deepEqual(preserved.data.availability, prior.data.availability);
assert.equal(preserved.data.availability_attempt, "unknown");
assert.deepEqual(mergeResult(prior, {error: "failed"}).data, prior.data);
assert.equal(refreshNotice(preserved, 2, preserved.data), "Latest provider check incomplete; previous availability shown.");
const failedRefresh = mergeResult(prior, {requestedId: 2, error: "failed"});
assert.equal(refreshNotice(failedRefresh, 2, failedRefresh.data), "Latest refresh failed; previous data shown.");
assert.equal(refreshNotice(failedRefresh, 2, null), "Latest refresh failed.");
assert.equal(refreshNotice(failedRefresh, 3, failedRefresh.data), null);
assert.equal(refreshNotice({requestedId: 2, data: prior.data, error: null}, 2, prior.data), null);
const calls = [], limitedEvents = [];
const limited = await runBatch(chosen, (id, signal) => fetchLiveMovie(id, signal, async () => {
  calls.push(id);
  return id === 2 ? {status: 429, ok: false} : {status: 200, ok: true, json: async () => ({tmdb_id: id, availability: {offers: []}})};
}), new AbortController().signal, (id, result) => limitedEvents.push([id, result]));
assert.deepEqual(limited, {succeeded: 1, failed: 1, cancelled: false, rateLimited: true});
assert.deepEqual(calls, [1, 2]);
assert.match(limitedEvents[1][1].error, /rate limit/i);
assert.deepEqual(mergeResult(prior, limitedEvents[1][1]).data, prior.data);
assert.deepEqual(chooseBatch(films, Object.fromEntries(limitedEvents), true).map((film) => film.id), ["task-1"]);
const retryEvents = [];
const retry = await runBatch(chooseBatch(films, Object.fromEntries(limitedEvents), true), async (id) => ({tmdb_id: id}), new AbortController().signal, (id, result) => retryEvents.push([id, result]));
assert.equal(retry.succeeded, 1);
assert.equal(mergeResult(limitedEvents[1][1], retryEvents[0][1]).error, null);
assert.equal(mergeResult({requestedId: 1, data: {tmdb_id: 1}}, {requestedId: 2, error: "unavailable"}).data, undefined, "a new ID must not retain old metadata after failure");
await assert.rejects(() => fetchLiveMovie(1, null, async () => ({status: 429})), RateLimitError);
const many = Array.from({length: 65}, (_, index) => ({id: `f-${index}`, fields: {"POC TMDB ID": String(index + 1)}}));
const remaining = chooseRemaining(many, {"f-0": {data: {tmdb_id: 1}}, "f-1": {requestedId: 2, error: "failed"}});
assert.equal(remaining.length, 63, "already loaded and failed entries are excluded");
let activeCalls = 0, maxActive = 0;
const progress = [];
const all = await runRemainingBatch(remaining, async (id) => {
  activeCalls++; maxActive = Math.max(maxActive, activeCalls);
  await Promise.resolve(); activeCalls--;
  return {tmdb_id: id};
}, new AbortController().signal, (id, result, done, total) => progress.push([id, done, total]));
assert.deepEqual(all, {succeeded: 63, failed: 0, rateLimited: false, cancelled: false});
assert.equal(maxActive, 1);
assert.deepEqual(progress.at(-1), ["f-64", 63, 63]);
for (const limitedFailure of [true, false]) {
  let count = 0;
  const stopped = await runRemainingBatch(many, async (id) => {
    count++;
    if (id === 32) throw limitedFailure ? new RateLimitError() : new Error("failure");
    return {tmdb_id: id};
  }, new AbortController().signal, () => {});
  assert.equal(count, 32, "both rate limits and other failures stop across chunk boundaries");
  assert.deepEqual(stopped, {succeeded: 31, failed: 1, rateLimited: limitedFailure, cancelled: false});
}
const stopController = new AbortController();
let cancelledRequests = 0, cancelledResults = 0;
const stopped = await runRemainingBatch(many, async (id) => {
  cancelledRequests++;
  if (id === 32) stopController.abort();
  return {tmdb_id: id};
}, stopController.signal, () => cancelledResults++);
assert.equal(cancelledRequests, 32);
assert.equal(cancelledResults, 31, "an in-flight result is discarded after cancellation");
assert.equal(stopped.cancelled, true);
console.log("Live enrichment batch limit, sequential failure, cancellation and retry passed");
