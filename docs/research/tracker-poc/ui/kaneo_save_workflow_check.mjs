import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {metadataChanges} from "./kaneo_metadata.js";
import {decodeStoredGenres} from "./stored_genres.js";

// Exercise the actual save handler without a browser or tracker credentials.
const source = readFileSync(new URL("./src.jsx", import.meta.url), "utf8");
const start = source.indexOf("  async function save(event) {");
const end = source.indexOf("  async function addFilm(event) {", start);
if (start < 0 || end < 0) throw new Error("Kaneo save handler not found");
const make = new Function("title", "description", "status", "tmdb", "year", "filmGenre", "film", "project", "setError", "setBusy", "metadataChanges", "metadataDirty", "filmFieldsDirty", "identityField", "request", "detailDirty", "refresh", `${source.slice(start, end)}; return save;`);

async function exercise({draft = {}, edited = {}, metadataEdited = {}, unavailable = false, failWrite = false} = {}) {
  const film = {id:"fictional-task",title:"New fictional title",status:"in-review",fields:{"POC TMDB ID":"200"},metadata:{
    year:{editable:true,fieldId:"year",value:"2001"},
    genre:{editable:!unavailable,fieldId:unavailable ? null : "genre",rawValue:"Drama",value:"Drama",status:"known"},
  }};
  const value = {title:"Old fictional title",description:"Old fictional synopsis",status:"to-do",tmdb:"100",year:"2001",genre:"Drama",...draft};
  const fieldDirty = {current:{title:false,description:false,status:false,tmdb:false,...edited}};
  const metadataDirty = {current:{year:false,genre:false,genreReset:false,...metadataEdited}};
  const detailDirty = {current:true}, writes = [];
  let identityChecks = 0, error = "", refreshed = false, backendSynopsis = "New enriched synopsis";
  const identityField = async () => { identityChecks++; return "identity"; };
  const request = async (path, method, body) => {
    writes.push({path,method,body});
    if (failWrite) throw new Error("Fictional write failed");
    if (path.startsWith("/task/description/")) backendSynopsis = body.description;
    return {};
  };
  const save = make(value.title, value.description, value.status, value.tmdb, value.year, value.genre, film, "fictional-project", (message) => {error = message;}, () => {}, metadataChanges, metadataDirty, fieldDirty, identityField, request, detailDirty, async () => {refreshed = true;});
  await save({preventDefault() {}});
  return {writes, identityChecks, error, refreshed, backendSynopsis, detailDirty:detailDirty.current, fieldDirty:fieldDirty.current, metadataDirty:metadataDirty.current};
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
console.log("Kaneo saves only edited fields and preserves background enrichment");
