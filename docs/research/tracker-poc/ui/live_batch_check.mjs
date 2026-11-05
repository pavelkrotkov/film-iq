import assert from "node:assert/strict";
import { BATCH_LIMIT, chooseBatch, mergeResult, runBatch } from "./live_batch.js";

const films = Array.from({length: 35}, (_, index) => ({
  id: `task-${index}`,
  fields: {"POC TMDB ID": String(index + 1)},
}));
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
assert.deepEqual(outcome, {succeeded: 1, failed: 1, cancelled: true});
assert.equal(events.length, 2);
assert.ok(events[1][1].error);
assert.equal(chooseBatch(films, {"task-0": {data: {}}, "task-1": {error: "failed"}})[0].id, "task-2");
assert.deepEqual(chooseBatch(films, {"task-1": {error: "failed"}}, true).map((film) => film.id), ["task-1"]);
const prior = {data: {availability: {status: "complete", offers: ["fixture"]}}};
const preserved = mergeResult(prior, {data: {availability: {status: "unknown", offers: []}}});
assert.deepEqual(preserved.data.availability, prior.data.availability);
assert.equal(preserved.data.availability_attempt, "unknown");
assert.deepEqual(mergeResult(prior, {error: "failed"}).data, prior.data);
console.log("Live enrichment batch limit, sequential failure, cancellation and retry passed");
