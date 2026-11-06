import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {filmBaseline, filmChanges, hasDuplicateTmdbId} from "./youtrack_edit.js";
import {decodeStoredGenres} from "./stored_genres.js";

// Exercise the installed save handler's data flow without a browser or credentials.
const source = readFileSync(new URL("./youtrack.jsx", import.meta.url), "utf8");
const start = source.indexOf("  async function saveFilm(event) {");
const end = source.indexOf("  async function savePreference(event) {", start);
if (start < 0 || end < 0) throw new Error("YouTrack save handler not found");
const make = new Function("film", "editBaseline", "setWorking", "setError", "filmChanges", "title", "synopsis", "state", "tmdbId", "releaseYear", "filmGenre", "genreReset", "hasDuplicateTmdbId", "getFilms", "project", "host", "refresh", "markFilmDirty", "setNotice", `${source.slice(start, end)}; return saveFilm;`);

const issue = (overrides = {}) => ({id:"fictional-issue",idReadable:"FILMPOC-1",summary:overrides.title ?? "Original title",description:overrides.synopsis ?? "Original synopsis",customFields:[
  {name:"FilmIQ TMDB ID",value:overrides.id ?? 101},
  {name:"FilmIQ Lifecycle",value:{name:overrides.state ?? "Discovery"}},
  {name:"FilmIQ Release Year",value:overrides.year ?? 2001},
  {name:"FilmIQ Genre",value:overrides.genre ?? "Drama"},
  {name:"FilmIQ Source Year",value:1999},
  {name:"FilmIQ Director",value:"Fictional Source Director"},
]});

async function exercise({draft = {}, failWrite = false} = {}) {
  const baseline = filmBaseline(issue());
  const backend = issue({title:"Enriched title",synopsis:"Enriched synopsis",id:202,state:"Evaluation",year:2002});
  const before = structuredClone(backend);
  const value = {title:baseline.title,synopsis:baseline.synopsis,state:baseline.state,tmdbId:String(baseline.tmdbId),releaseYear:String(baseline.releaseYear),genre:baseline.genre,genreReset:false,...draft};
  let error = "", notice = "", dirty = true, refreshed = false;
  const writes = [];
  const host = {fetchYouTrack:async (path, options) => {
    writes.push({path,options});
    if (failWrite) throw new Error("Fictional write failure");
    const body = options.body;
    if (Object.hasOwn(body,"summary")) backend.summary = body.summary;
    if (Object.hasOwn(body,"description")) backend.description = body.description;
    for (const field of body.customFields || []) backend.customFields.find((item) => item.name === field.name).value = field.value;
    return {};
  }};
  const save = make(backend, baseline, () => {}, (message) => {error=message;}, filmChanges, value.title, value.synopsis, value.state, value.tmdbId, value.releaseYear, value.genre, value.genreReset, hasDuplicateTmdbId, async () => [backend], "FILMPOC", host, async () => {refreshed=true; return true;}, (value) => {dirty=value;}, (message) => {notice=message;});
  await save({preventDefault() {}});
  return {before, backend, writes, error, notice, dirty, refreshed};
}

const genreOnly = await exercise({draft:{genre:"Drama\nComedy"}});
assert.equal(genreOnly.writes.length,1);
assert.deepEqual(Object.keys(genreOnly.writes[0].options.body),["customFields"]);
assert.deepEqual(decodeStoredGenres(genreOnly.backend.customFields.find((item) => item.name === "FilmIQ Genre").value).genres,["Drama","Comedy"]);
assert.equal(genreOnly.backend.summary,genreOnly.before.summary);
assert.equal(genreOnly.backend.description,genreOnly.before.description);
for (const name of ["FilmIQ TMDB ID","FilmIQ Lifecycle","FilmIQ Release Year","FilmIQ Source Year","FilmIQ Director"]) {
  assert.deepEqual(genreOnly.backend.customFields.find((item) => item.name === name),genreOnly.before.customFields.find((item) => item.name === name),`${name} must not be overwritten`);
}
assert.equal(genreOnly.dirty,false); assert.equal(genreOnly.refreshed,true);
for (const [field, value, expected] of [["title","Edited title","summary"],["synopsis","Edited synopsis","description"],["state","Archived","FilmIQ Lifecycle"],["tmdbId","303","FilmIQ TMDB ID"],["releaseYear","2003","FilmIQ Release Year"],["releaseYear","","FilmIQ Release Year"],["genre","","FilmIQ Genre"]]) {
  const result = await exercise({draft:{[field]:value}});
  assert.equal(result.writes.length,1);
  const body = result.writes[0].options.body;
  assert.deepEqual(Object.keys(body),[field === "title" || field === "synopsis" ? expected : "customFields"]);
  if (body.customFields) {
    assert.deepEqual(body.customFields.map((item) => item.name),[expected]);
    if (!value) assert.equal(body.customFields[0].value,null,"explicit clears remain null");
  }
}
const invalid = await exercise({draft:{tmdbId:""}});
assert.equal(invalid.writes.length,0); assert.match(invalid.error,/clearing.*not supported/i); assert.equal(invalid.dirty,true);
const failed = await exercise({draft:{synopsis:"Edited synopsis"},failWrite:true});
assert.equal(failed.writes.length,1); assert.match(failed.error,/may have completed/i); assert.equal(failed.dirty,true);
console.log("YouTrack actual save handler preserves unrelated background-enriched fields");
