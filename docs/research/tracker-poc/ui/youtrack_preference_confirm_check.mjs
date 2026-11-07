import assert from "node:assert/strict";
import {readFileSync} from "node:fs";

const source = readFileSync(new URL("./youtrack.jsx", import.meta.url), "utf8");
const start = source.indexOf("  async function confirmPreference() {");
const end = source.indexOf("  async function discardPreference() {", start);
const sameStart = source.indexOf("export function samePreference(");
const sameEnd = source.indexOf("\n// The YouTrack full-page widget iframe", sameStart);
assert(start >= 0 && end > start, "YouTrack confirmation handler must exist");
assert(sameStart >= 0 && sameEnd > sameStart, "Preference comparison must exist");
const samePreference = new Function(`${source.slice(sameStart, sameEnd).replace("export function", "function")}; return samePreference;`)();

const before = {interest_score: 4, watchlist: false, watched_at: null, personal_notes: "old"};
const after = {interest_score: 8, watchlist: true, watched_at: null, personal_notes: "new"};
const target = "FILMPOC-1";
const preview = {issue_id: target, before, after};

async function run({response, read, failWrite = false, selectionChanges = false} = {}) {
  let preferences = {[target]: before, "FILMPOC-2": before}, dirty = true;
  let pending = preview, uncertain = false, discardFailed = false, error = "", notice = "";
  const selectedRef = {current: target};
  const host = {fetchApp: async () => {
    if (failWrite) throw new Error("response lost");
    if (selectionChanges) selectedRef.current = "FILMPOC-2";
    return response ?? {issue_id: target, recorded: true, preference: after};
  }};
  const readPreferences = async () => {
    if (read === "failed") throw new Error("read unavailable");
    if (read === "missing") return {"FILMPOC-2": before};
    if (read === "stale") return {[target]: before, "FILMPOC-2": before};
    return {[target]: after, "FILMPOC-2": before};
  };
  const make = new Function("previewMatchesFilm", "pendingPreview", "selectedRef", "setWorking", "setError", "host", "setPreview", "setDiscardFailed", "setSaveUncertain", "setPreferences", "readPreferences", "markPrefDirty", "setNotice", "samePreference", `${source.slice(start, end)}; return confirmPreference;`);
  const confirm = make((p, id) => p?.issue_id === id && !!p.after, preview, selectedRef, () => {}, (value) => {error = value;}, host,
    (value) => {pending = value;}, (value) => {discardFailed = value;}, (value) => {uncertain = value;},
    (value) => {preferences = typeof value === "function" ? value(preferences) : value;}, readPreferences,
    (value) => {dirty = value;}, (value) => {notice = value;}, samePreference);
  await confirm();
  return {preferences, dirty, pending, uncertain, discardFailed, error, notice};
}

const success = await run();
assert.deepEqual(success.preferences[target], after); assert.equal(success.dirty, false);
for (const read of ["failed", "missing", "stale"]) {
  const result = await run({read});
  assert.deepEqual(result.preferences[target], after, `retain confirmed value after ${read} read`);
  assert.deepEqual(result.preferences["FILMPOC-2"], before);
  assert.equal(result.dirty, false); assert.equal(result.pending, null);
  assert.match(result.error, /saved.*refresh/i);
}
for (const response of [{}, {issue_id:target, recorded:true}, {issue_id: "FILMPOC-2", recorded:true, preference:after}, {issue_id:target, recorded:true, preference:before}]) {
  const result = await run({response});
  assert.deepEqual(result.preferences[target], before); assert.equal(result.dirty, true);
  assert.equal(result.uncertain, true); assert.equal(result.discardFailed, true);
  assert.match(result.error, /may have completed/i);
}
const failed = await run({failWrite:true});
assert.equal(failed.dirty, true); assert.equal(failed.uncertain, true);
const changedSelection = await run({selectionChanges:true});
assert.deepEqual(changedSelection.preferences[target], after);
assert.equal(changedSelection.dirty, true, "confirming an earlier film must not clear the new film's draft");
assert.match(source, /const locked = busy \|\| loadingFilms/);
assert.match(source, /<label>Local POC watchlist<select disabled=\{locked\}/);
assert.match(source, /<label>Personal notes<textarea disabled=\{locked\}/);
console.log("YouTrack preference confirmation preserves acknowledged values and uncertain drafts");
