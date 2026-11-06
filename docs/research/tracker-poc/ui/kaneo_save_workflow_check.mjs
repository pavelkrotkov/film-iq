import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {metadataChanges} from "./kaneo_metadata.js";
import {decodeStoredGenres} from "./stored_genres.js";

// Exercise the actual save handler without a browser or tracker credentials.
const source = readFileSync(new URL("./src.jsx", import.meta.url), "utf8");
const start = source.indexOf("  async function save(event) {");
const end = source.indexOf("  async function addFilm(event) {", start);
const refreshStart = source.indexOf("  async function refresh() {");
const refreshEnd = source.indexOf("  async function refreshProjects() {", refreshStart);
if (start < 0 || end < 0 || refreshStart < 0 || refreshEnd < 0) throw new Error("Kaneo save or refresh handler not found");
const make = new Function("title", "description", "status", "tmdb", "year", "filmGenre", "film", "project", "setError", "setBusy", "metadataChanges", "metadataDirty", "filmFieldsDirty", "identityField", "request", "detailDirty", "refresh", "loaded", "detailReady", "setLoaded", `${source.slice(start, end)}; return save;`);
const makeRefresh = new Function("project", "setBusy", "setError", "load", "setFilms", "cacheFixture", "fixtureIds", "tmdbId", "setLoaded", "setStates", "setDefaultState", "preferenceRequest", "setPreferences", "setMovary", `${source.slice(refreshStart, refreshEnd)}; return refresh;`);

async function exercise({draft = {}, edited = {}, metadataEdited = {}, unavailable = false, failWrite = false, failAt = 0, reloadFailure = false, preferencesFailure = false, initiallyLoaded = true, baselineTitle = "New fictional title"} = {}) {
  const film = {id:"fictional-task",title:baselineTitle,status:"in-review",fields:{"POC TMDB ID":"200"},metadata:{
    year:{editable:true,fieldId:"year",value:"2001"},
    genre:{editable:!unavailable,fieldId:unavailable ? null : "genre",rawValue:"Drama",value:"Drama",status:"known"},
  }};
  const value = {title:"Old fictional title",description:"Old fictional synopsis",status:"to-do",tmdb:"100",year:"2001",genre:"Drama",...draft};
  const fieldDirty = {current:{title:false,description:false,status:false,tmdb:false,...edited}};
  const metadataDirty = {current:{year:false,genre:false,genreReset:false,...metadataEdited}};
  const detailDirty = {current:true}, writes = [];
  let identityChecks = 0, error = "", refreshed = false, loaded = initiallyLoaded, busy = false, backendTitle = film.title, backendSynopsis = "New enriched synopsis";
  const setError = (message) => {error = message;};
  const setBusy = (value) => {busy = value;};
  const identityField = async () => { identityChecks++; return "identity"; };
  const request = async (path, method, body) => {
    writes.push({path,method,body});
    if (failWrite || failAt === writes.length) throw new Error("Fictional write failed");
    if (path.startsWith("/task/title/")) backendTitle = body.title;
    if (path.startsWith("/task/description/")) backendSynopsis = body.description;
    return {};
  };
  const refresh = makeRefresh("fictional-project", setBusy, setError,
    async () => {refreshed = true; if (reloadFailure) throw new Error("Fictional reload failed"); return {films:[], states:{}, defaultState:"to-do"};},
    () => {}, false, new Set(), () => null, (value) => {loaded = value;}, () => {}, () => {},
    async (path) => {if (preferencesFailure && path === "/preferences") throw new Error("Fictional preferences unavailable"); return path === "/preferences" ? {preferences:{}} : {};},
    () => {}, () => {});
  const save = make(value.title, value.description, value.status, value.tmdb, value.year, value.genre, film, "fictional-project", setError, setBusy, metadataChanges, metadataDirty, fieldDirty, identityField, request, detailDirty, refresh, initiallyLoaded, true, (value) => {loaded = value;});
  await save({preventDefault() {}});
  return {writes, identityChecks, error, refreshed, loaded, busy, backendTitle, backendSynopsis, detailDirty:detailDirty.current, fieldDirty:fieldDirty.current, metadataDirty:metadataDirty.current};
}

const genreOnly = await exercise({draft:{genre:"Drama\nComedy"},metadataEdited:{genre:true}});
assert.deepEqual(genreOnly.writes.map((item) => item.path), ["/custom-field/value"]);
assert.deepEqual(decodeStoredGenres(genreOnly.writes[0].body.value).genres, ["Drama","Comedy"]);
assert.equal(genreOnly.backendSynopsis, "New enriched synopsis", "an unrelated save must not overwrite enrichment");
assert.equal(genreOnly.identityChecks, 0, "a background ID change must not be reverted");
assert.equal(genreOnly.detailDirty, false); assert.equal(genreOnly.refreshed, true);
const newBackgroundId = await exercise({draft:{tmdb:"",genre:"Comedy"},metadataEdited:{genre:true}});
assert.equal(newBackgroundId.error, "", "a newly enriched ID must not block an unrelated edit");
assert.deepEqual(newBackgroundId.writes.map((item) => item.path), ["/custom-field/value"]);
for (const [field, value, expected] of [
  ["title", "Changed title", "/task/title/fictional-task"],
  ["description", "Changed synopsis", "/task/description/fictional-task"],
  ["status", "archived", "/task/status/fictional-task"],
  ["tmdb", "300", "/custom-field/value"],
]) {
  const result = await exercise({draft:{[field]:value}, edited:{[field]:true}});
  assert.deepEqual(result.writes.map((item) => item.path), [expected], `${field} should update only its own field`);
  assert.equal(result.identityChecks, field === "tmdb" ? 1 : 0);
}
const missingField = await exercise({draft:{genre:"Comedy"},metadataEdited:{genre:true},unavailable:true});
assert.deepEqual(missingField.writes, []); assert.match(missingField.error, /draft is unsaved/i); assert.equal(missingField.detailDirty, true);
const blankId = await exercise({draft:{tmdb:""},edited:{tmdb:true}});
assert.deepEqual(blankId.writes, []); assert.match(blankId.error, /cannot be cleared/i); assert.equal(blankId.detailDirty, true);
const failed = await exercise({draft:{description:"Changed synopsis"},edited:{description:true},failWrite:true});
assert.match(failed.error, /may be partial/i); assert.equal(failed.fieldDirty.description, true); assert.equal(failed.detailDirty, true);
assert.equal(failed.refreshed,false); assert.equal(failed.loaded,false); assert.equal(failed.busy,false);
const partial = await exercise({draft:{title:"New title",description:"New synopsis"},edited:{title:true,description:true},failAt:2});
assert.equal(partial.backendTitle,"New title"); assert.equal(partial.backendSynopsis,"New enriched synopsis");
assert.match(partial.error,/may be partial/i); assert.equal(partial.refreshed,false); assert.equal(partial.loaded,false); assert.equal(partial.detailDirty,true);
assert.equal(partial.fieldDirty.title,true); assert.equal(partial.fieldDirty.description,true);
const savedReadFailed = await exercise({draft:{description:"User-entered synopsis"},edited:{description:true},reloadFailure:true});
assert.equal(savedReadFailed.backendSynopsis,"User-entered synopsis"); assert.equal(savedReadFailed.loaded,false);
assert.match(savedReadFailed.error,/changes saved.*could not be reloaded/i);
assert.equal(savedReadFailed.detailDirty,false); assert.equal(savedReadFailed.busy,false);
const noChangeReadFailed = await exercise({reloadFailure:true});
assert.deepEqual(noChangeReadFailed.writes,[]); assert.equal(noChangeReadFailed.error,"Fictional reload failed");
const optionalReadFailed = await exercise({draft:{description:"Saved"},edited:{description:true},preferencesFailure:true});
assert.equal(optionalReadFailed.loaded,true); assert.match(optionalReadFailed.error,/preferences are unavailable/i);
assert.doesNotMatch(optionalReadFailed.error,/changes saved.*could not be reloaded/i);
// A failed reload cannot leave an editable old baseline that silently skips a
// later change back to the old displayed title.
const changedThenReloadFailed = await exercise({draft:{title:"Saved title"},edited:{title:true},reloadFailure:true});
assert.equal(changedThenReloadFailed.backendTitle,"Saved title"); assert.equal(changedThenReloadFailed.loaded,false);
const blockedStaleRetry = await exercise({draft:{title:"New fictional title"},edited:{title:true},initiallyLoaded:false});
assert.deepEqual(blockedStaleRetry.writes,[]); assert.match(blockedStaleRetry.error,/reload films before saving/i);
assert.equal(blockedStaleRetry.detailDirty,true); assert.equal(blockedStaleRetry.fieldDirty.title,true);
const afterReload = await exercise({baselineTitle:"Saved title",draft:{title:"New fictional title"},edited:{title:true}});
assert.equal(afterReload.backendTitle,"New fictional title");
assert.deepEqual(afterReload.writes.map((item) => item.path),["/task/title/fictional-task"]);
assert.match(source,/disabled=\{busy \|\| !loaded \|\| !detailReady\}>Save to Kaneo/);
assert.match(source,/onClick=\{refresh\}>Reload films/);
console.log("Kaneo saves only edited fields and preserves background enrichment");
