import assert from "node:assert/strict";
import { boundedRead, loadFilmView, publishFilmBatch } from "./youtrack_loading.js";

const never = () => new Promise(() => {});
await assert.rejects(boundedRead(never, 15, "Project lookup timed out"), /Project lookup timed out/);
let loading = true, films = null;
const sequence = {current: 1};
const stalledView = loadFilmView({
  loadFilms: async () => [{id: "fictional"}],
  loadPreferences: never,
  loadWatched: never,
  publishFilms: (value) => publishFilmBatch(1, sequence, value, (v) => { films = v; }, (v) => { loading = v; }),
}, 15);
await Promise.resolve();
assert.equal(loading, false, "canonical cards must unlock while optional data is still pending");
assert.deepEqual(films, [{id: "fictional"}]);
await stalledView;
loading = true;
sequence.current = 2;
publishFilmBatch(1, sequence, [{id: "stale"}], (v) => { films = v; }, (v) => { loading = v; });
assert.equal(loading, true, "a stale response must not unlock a newer project load");
assert.deepEqual(films, [{id: "fictional"}], "a stale response must not replace current films");
for (const stalled of ["preferences", "watched"]) {
  let published = null;
  const promise = loadFilmView({
    loadFilms: async () => [{id:"fictional"}],
    loadPreferences: stalled === "preferences" ? never : async () => ({preferences:{}}),
    loadWatched: stalled === "watched" ? never : async () => ({status:"available",films:{}}),
    publishFilms: (films) => { published = films; },
  }, 15);
  await Promise.resolve();
  assert.deepEqual(published, [{id:"fictional"}], "canonical films must publish before optional requests settle");
  const results = await promise;
  const failedIndex = stalled === "preferences" ? 0 : 1;
  assert.equal(results[failedIndex].status, "rejected", "stalled optional read must time out");
  assert.equal(results[1-failedIndex].status, "fulfilled", "other optional read must retain its result");
}
let published = false;
await assert.rejects(loadFilmView({loadFilms:async () => {throw new Error("film failure");},loadPreferences:never,loadWatched:never,publishFilms:()=>{published=true;}},15));
assert.equal(published,false,"failed film loading cannot publish empty results as success");
console.log("Canonical films publish despite stalled optional reads; timeouts remain unavailable");
