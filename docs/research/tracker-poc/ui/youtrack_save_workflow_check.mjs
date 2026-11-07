import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {filmBaseline, filmChanges, hasDuplicateTmdbId} from "./youtrack_edit.js";
import {decodeStoredGenres} from "./stored_genres.js";

// Exercise the installed save handler's data flow without a browser or credentials.
const source = readFileSync(new URL("./youtrack.jsx", import.meta.url), "utf8");
const start = source.indexOf("  async function saveFilm(event) {");
const end = source.indexOf("  async function savePreference(event) {", start);
if (start < 0 || end < 0) throw new Error("YouTrack save handler not found");
const make = new Function("film", "editBaseline", "setWorking", "setError", "filmChanges", "title", "synopsis", "state", "tmdbId", "releaseYear", "filmGenre", "genreReset", "hasDuplicateTmdbId", "getFilms", "project", "host", "refresh", "markFilmDirty", "setNotice", "filmNeedsReload", "setFilmNeedsReload", "selectedRef", "projectRef", `${source.slice(start, end)}; return {saveFilm, reloadFilmAndDiscardDraft};`);

const issue = (overrides = {}) => ({id:"fictional-issue",idReadable:"FILMPOC-1",summary:overrides.title ?? "Original title",description:overrides.synopsis ?? "Original synopsis",customFields:[
  {name:"FilmIQ TMDB ID",value:overrides.id ?? 101},
  {name:"FilmIQ Lifecycle",value:{name:overrides.state ?? "Discovery"}},
  {name:"FilmIQ Release Year",value:overrides.year ?? 2001},
  {name:"FilmIQ Genre",value:overrides.genre ?? "Drama"},
  {name:"FilmIQ Source Year",value:1999},
  {name:"FilmIQ Director",value:"Fictional Source Director"},
]});

async function exercise({draft = {}, failWrite = false, needsReload = false, failReload = false, contextChange = false, recovery = false} = {}) {
  const baseline = filmBaseline(issue());
  const backend = issue({title:"Enriched title",synopsis:"Enriched synopsis",id:202,state:"Evaluation",year:2002});
  const before = structuredClone(backend);
  const value = {title:baseline.title,synopsis:baseline.synopsis,state:baseline.state,tmdbId:String(baseline.tmdbId),releaseYear:String(baseline.releaseYear),genre:baseline.genre,genreReset:false,...draft};
  let error = "", notice = "", dirty = true, refreshed = false, guarded = needsReload;
  const selectedRef = {current:backend.idReadable}, projectRef = {current:"FILMPOC"};
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
  const handlers = make(backend, baseline, () => {}, (message) => {error=message;}, filmChanges, value.title, value.synopsis, value.state, value.tmdbId, value.releaseYear, value.genre, value.genreReset, hasDuplicateTmdbId, async () => [backend], "FILMPOC", host, async () => {refreshed=true; if (contextChange) selectedRef.current="FILMPOC-2"; return !failReload;}, (value) => {dirty=value;}, (message) => {notice=message;}, needsReload, (value) => {guarded=value;}, selectedRef, projectRef);
  if (recovery) await handlers.reloadFilmAndDiscardDraft();
  else await handlers.saveFilm({preventDefault() {}});
  return {before, backend, writes, error, notice, dirty, refreshed, guarded};
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
assert.equal(failed.writes.length,1); assert.match(failed.error,/may have completed/i); assert.equal(failed.dirty,true); assert.equal(failed.guarded,true);
const savedWithoutRead = await exercise({draft:{title:"Saved title"},failReload:true});
assert.equal(savedWithoutRead.backend.summary,"Saved title"); assert.equal(savedWithoutRead.dirty,true); assert.equal(savedWithoutRead.guarded,true);
assert.match(savedWithoutRead.error,/saved.*refresh failed/i);
const blocked = await exercise({draft:{title:"Original title"},needsReload:true});
assert.equal(blocked.writes.length,0); assert.equal(blocked.dirty,true); assert.match(blocked.error,/discard.*draft/i);
const recoveryFails = await exercise({needsReload:true,recovery:true,failReload:true});
assert.equal(recoveryFails.dirty,true); assert.equal(recoveryFails.guarded,true);
const recoveryMoves = await exercise({needsReload:true,recovery:true,contextChange:true});
assert.equal(recoveryMoves.dirty,true); assert.equal(recoveryMoves.guarded,true);
const recovered = await exercise({needsReload:true,recovery:true});
assert.equal(recovered.dirty,false); assert.equal(recovered.guarded,false); assert.match(recovered.notice,/draft was discarded/i);
// Discarding a draft while changing routes does not make a stale cached film safe to edit.
const navigateStart = source.indexOf("  async function navigateRoute(next) {");
const navigateEnd = source.indexOf("  async function selectFilm(id, discard = false) {", navigateStart);
assert.ok(navigateStart >= 0 && navigateEnd > navigateStart);
const selectedRef = {current:"FILMPOC-1"}, projectRef = {current:"FILMPOC"};
let routeGuard = true;
const navigate = new Function("markFilmDirty", "markPrefDirty", "setFilmNeedsReload", "setNewFilmTitle", "setNewFilmTmdbId", "projectRef", "selectedRef", "setProject", "setSelected", "host", "routeLocation", "setError", `${source.slice(navigateStart, navigateEnd)}; return navigateRoute;`)(
  () => {}, () => {}, (value) => {routeGuard=value;}, () => {}, () => {}, projectRef, selectedRef, () => {}, () => {}, {navigation:{updateAppLocation:async () => {}}}, (value) => value, () => {},
);
await navigate({project:"FILMPOC",film:null});
await navigate({project:"OTHER",film:null});
await navigate({project:"FILMPOC",film:"FILMPOC-1"});
assert.equal(routeGuard,true,"navigation must not clear an uncertain film's reload guard");
assert.equal((await exercise({needsReload:routeGuard,draft:{title:"Original title"}})).writes.length,0);
assert.match(source,/readOnly=\{filmNeedsReload\}/); assert.match(source,/Reload films and discard film draft/);
console.log("YouTrack actual save handler preserves unrelated background-enriched fields");
