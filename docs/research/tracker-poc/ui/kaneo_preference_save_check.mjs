import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {markPreferenceSaved} from "./preference_draft.js";

// Exercise the actual preference handler with fictional in-memory responses.
const source = readFileSync(new URL("./src.jsx", import.meta.url), "utf8");
const start = source.indexOf("  async function savePreference(event) {");
const end = source.indexOf("  async function save(event) {", start);
if (start < 0 || end < 0) throw new Error("Preference save handler missing");
const make = new Function("film", "preference", "preferenceRequest", "setBusy", "setError", "setPreferences", "setPreferenceDraft", "markPreferenceSaved", "window", `${source.slice(start, end)}; return savePreference;`);

async function exercise({getFails = false, malformedGet = false, putFails = false, badPut = null, badGet = null, editDuringPut = false} = {}) {
  const film = {id: "fictional"};
  const old = {interest_score: 2, watchlist: false, watched_at: null, personal_notes: "old"};
  const submitted = {...old, interest_score: 8};
  const later = {...submitted, personal_notes: "later edit"};
  let preferences = {[film.id]: old, other: old}, draft = {filmId:film.id,value:submitted,dirty:true};
  let error = "", busy = false, writes = 0;
  const request = async (path, method) => {
    if (path.startsWith("/preview/")) return {before:old, after:submitted, token:"fictional"};
    if (method === "PUT") {
      writes++;
      if (editDuringPut) draft = {filmId:film.id,value:later,dirty:true};
      if (putFails) throw new Error("Fictional response lost");
      return {preference: badPut ?? submitted};
    }
    if (getFails) throw new Error("Fictional read failure");
    if (malformedGet) return {};
    if (badGet) return {preferences: badGet === "missing" ? {other:old} : {[film.id]:old, other:old}};
    return {preferences: {[film.id]: submitted, other: old}};
  };
  const setPreferences = update => {preferences = typeof update === "function" ? update(preferences) : update;};
  const setDraft = update => {draft = typeof update === "function" ? update(draft) : update;};
  const save = make(film, submitted, request, value => {busy=value;}, value => {error=value;}, setPreferences, setDraft, markPreferenceSaved, {confirm:() => true});
  await save({preventDefault(){}});
  return {preferences,draft,error,busy,writes,submitted,later,old};
}
const saved = await exercise({getFails:true});
assert.equal(saved.writes, 1);
assert.deepEqual(saved.preferences.fictional, saved.submitted);
assert.deepEqual(saved.preferences.other, saved.old);
assert.equal(saved.draft.dirty, false);
assert.match(saved.error, /saved.*(refresh|reload)/i);
assert.equal(saved.busy, false);
const malformed = await exercise({malformedGet:true});
assert.deepEqual(malformed.preferences.fictional, malformed.submitted);
assert.equal(malformed.draft.dirty, false);
assert.match(malformed.error, /saved.*(refresh|reload)/i);
const later = await exercise({getFails:true, editDuringPut:true});
assert.equal(later.draft.dirty, true);
assert.deepEqual(later.draft.value, later.later);
const unconfirmed = await exercise({putFails:true});
assert.equal(unconfirmed.draft.dirty, true);
assert.deepEqual(unconfirmed.preferences.fictional, unconfirmed.old);
assert.match(unconfirmed.error, /(unconfirmed|could not confirm|may have saved)/i);
for (const badPut of [{}, {interest_score:8}, {...saved.submitted, interest_score:9}]) {
  const result = await exercise({badPut});
  assert.equal(result.draft.dirty, true);
  assert.deepEqual(result.preferences.fictional, result.old);
  assert.match(result.error, /(unconfirmed|could not confirm|may have saved)/i);
}
for (const badGet of ["missing", "different"]) {
  const result = await exercise({badGet});
  assert.equal(result.draft.dirty, false);
  assert.deepEqual(result.preferences.fictional, result.submitted);
  assert.match(result.error, /saved.*(refresh|reload)/i);
}
const complete = await exercise();
assert.equal(complete.draft.dirty, false);
assert.deepEqual(complete.preferences.fictional, complete.submitted);
assert.equal(complete.error, "");
console.log("Kaneo preference saves report readback failure while preserving drafts");
