import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {boundedRead} from "./youtrack_loading.js";

// Exercise the actual Kaneo refresh with fictional, stalled sidecar reads.
const source = readFileSync(new URL("./src.jsx", import.meta.url), "utf8");
const start = source.indexOf("  async function refresh() {");
const end = source.indexOf("  async function refreshProjects() {", start);
assert.ok(start >= 0 && end > start, "Kaneo refresh handler must exist");
const helperStart = source.indexOf("async function boundedPreferenceRead(path) {");
const helperEnd = source.indexOf("async function load(project) {", helperStart);
assert.ok(helperStart >= 0 && helperEnd > helperStart, "Bounded preference read must exist");
const makeRead = new Function("preferenceRequest", "boundedRead",
  `${source.slice(helperStart, helperEnd)}; return boundedPreferenceRead;`);
const make = new Function("project", "cacheFixture", "load", "fixtureIds", "tmdbId",
  "boundedPreferenceRead", "setBusy", "setError", "setFilms", "setLoaded",
  "setStates", "setDefaultState", "setPreferences", "setMovary",
  `${source.slice(start, end)}; return refresh;`);

for (const stalled of ["preferences", "movary"]) {
  const state = {busy:false};
  const result = {films:[{id:"fictional"}], states:{}, defaultState:"to-do"};
  const requests = [], signals = [];
  const read = makeRead(
    (path, method, body, signal) => {
      requests.push(path); signals.push(signal);
      if (path === (stalled === "preferences" ? "/preferences" : "/movary/fictional"))
        return new Promise(() => {});
      return Promise.resolve(path === "/preferences" ? {preferences:{}} : {status:"available", films:{}});
    }, (operation) => boundedRead(operation, 15));
  const refresh = make("fictional", false, async () => result, new Set(), () => 0,
    read,
    (value) => {state.busy = value;}, (value) => {state.error = value;},
    (value) => {state.films = value;}, (value) => {state.loaded = value;},
    (value) => {state.states = value;}, (value) => {state.defaultState = value;},
    (value) => {state.preferences = value;}, (value) => {state.movary = value;});
  const outcome = await Promise.race([refresh(), new Promise((resolve) => setTimeout(() => resolve("stalled"), 80))]);
  assert.equal(outcome, true, `${stalled} must not stall film loading indefinitely`);
  assert.equal(state.busy, false, `${stalled} must not freeze navigation`);
  assert.equal(state.loaded, true);
  assert.deepEqual(state.films, result.films);
  assert.ok(requests.includes("/preferences") && requests.includes("/movary/fictional"));
  assert.ok(signals.every((signal) => signal.aborted), "completed and stalled reads are released");
  if (stalled === "preferences") {
    assert.equal(state.preferences, null);
    assert.equal(state.movary.status, "available");
    assert.match(state.error, /preferences.*unavailable/i);
  } else {
    assert.deepEqual(state.preferences, {});
    assert.equal(state.movary, null);
  }
}
console.log("Kaneo film loading remains usable after fictional optional reads time out");
