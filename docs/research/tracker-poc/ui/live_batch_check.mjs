import assert from "node:assert/strict";
import { BATCH_LIMIT, chooseBatch, fetchLiveMovie, mergeResult, RateLimitError, runBatch, safeImdbTitleUrl } from "./live_batch.js";

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
assert.equal(chooseBatch(films, {"task-0": {data: {}}, "task-1": {error: "failed"}})[0].id, "task-2");
assert.deepEqual(chooseBatch(films, {"task-1": {error: "failed"}}, true).map((film) => film.id), ["task-1"]);
const prior = {data: {availability: {status: "complete", offers: ["fixture"]}}};
const preserved = mergeResult(prior, {data: {availability: {status: "unknown", offers: []}}});
assert.deepEqual(preserved.data.availability, prior.data.availability);
assert.equal(preserved.data.availability_attempt, "unknown");
assert.deepEqual(mergeResult(prior, {error: "failed"}).data, prior.data);
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
await assert.rejects(() => fetchLiveMovie(1, null, async () => ({status: 429})), RateLimitError);
console.log("Live enrichment batch limit, sequential failure, cancellation and retry passed");
