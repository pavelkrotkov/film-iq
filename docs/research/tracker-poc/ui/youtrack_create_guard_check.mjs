import assert from "node:assert/strict";
import {readFileSync} from "node:fs";

const source = readFileSync(new URL("./youtrack.jsx", import.meta.url), "utf8");
const start = source.indexOf("  async function addFilm(event) {");
const end = source.indexOf("  async function loadLiveMetadata() {", start);
const reviewStart = source.indexOf("  async function reviewCreate() {", start);
assert(start >= 0 && reviewStart > start && reviewStart < end, "creation review handler must exist");

async function run({uncertain = false, failCreate = false, refreshResult = true, response = {idReadable:"FILMPOC-9"}} = {}) {
  let creates = 0, title = "Fictional film", tmdb = "", error = "", guard = uncertain, checked = true, origin = null, selected = null;
  const host = {fetchYouTrack: async (path) => {
    if (path === "issues") { creates++; if (failCreate) throw new Error("Lost response"); return response; }
    return {id:"project-id"};
  }};
  const make = new Function("newTitle", "newTmdbId", "project", "createUncertain", "setWorking", "setError", "setNotice", "parseOptionalTmdbId", "hasDuplicateTmdbId", "getFilms", "boundedRead", "host", "setNewFilmTitle", "setNewFilmTmdbId", "refresh", "selectFilm", "setCreateUncertain", "setCreateChecked", "setCreateProject", `${source.slice(start,reviewStart)}; return addFilm;`);
  const add = make(title,tmdb,"FILMPOC",uncertain,()=>{},(v)=>{error=v;},()=>{},()=>null,()=>false,async()=>[],(f)=>f(),host,(v)=>{title=v;},(v)=>{tmdb=v;},async()=>refreshResult,async(v)=>{selected=v;},(v)=>{guard=v;},(v)=>{checked=v;},(v)=>{origin=v;});
  await add({preventDefault() {}});
  return {creates,title,tmdb,error,guard,checked,origin,selected};
}

const blocked = await run({uncertain:true});
assert.equal(blocked.creates,0); assert.equal(blocked.title,"Fictional film");
const failed = await run({failCreate:true});
assert.equal(failed.creates,1); assert.equal(failed.guard,true); assert.equal(failed.checked,false); assert.equal(failed.origin,"FILMPOC");
assert.equal(failed.title,"Fictional film"); assert.match(failed.error,/may have completed/i);
const incomplete = await run({response:{}});
assert.equal(incomplete.guard,true); assert.equal(incomplete.title,"Fictional film");
const reloadFailed = await run({refreshResult:false});
assert.equal(reloadFailed.creates,1); assert.equal(reloadFailed.guard,true); assert.equal(reloadFailed.checked,false); assert.equal(reloadFailed.origin,"FILMPOC");
assert.equal(reloadFailed.title,"Fictional film"); assert.match(reloadFailed.error,/created.*refresh failed/i);
const success = await run();
assert.equal(success.creates,1); assert.equal(success.title,""); assert.equal(success.selected,"FILMPOC-9");

let checked = false, guard = true, origin = "FILMPOC", reloadWorks = false, message = "", project = "FILMPOC";
const projectRef = {current:"FILMPOC"};
const makeReview = new Function("createChecked", "createProject", "setCreateChecked", "setCreateUncertain", "setCreateProject", "setError", "refresh", "project", "projectRef", "setWorking", `${source.slice(reviewStart,end)}; return {reviewCreate, allowCreateRetry};`);
const handlers = () => makeReview(checked,origin,(v)=>{checked=v;},(v)=>{guard=v;},(v)=>{origin=v;},(v)=>{message=v;},async()=>reloadWorks,project,projectRef,()=>{});
await handlers().reviewCreate(); handlers().allowCreateRetry();
assert.equal(checked,false); assert.equal(guard,true,"failed reload must not permit retry");
reloadWorks=true; await handlers().reviewCreate();
assert.equal(checked,true); assert.equal(guard,true,"successful reload still requires explicit confirmation");
assert.match(message,/check the film list/i);
project="FILMREAL"; projectRef.current=project;
await handlers().reviewCreate(); handlers().allowCreateRetry();
assert.equal(guard,true,"another project cannot clear the original project's guard");
assert.match(message,/original project/i);
project="FILMPOC"; projectRef.current=project; handlers().allowCreateRetry();
assert.equal(guard,false); assert.equal(checked,false);
guard=true; origin="FILMPOC"; checked=false; projectRef.current="FILMPOC";
const changedDuringReload = makeReview(false,origin,(v)=>{checked=v;},(v)=>{guard=v;},(v)=>{origin=v;},(v)=>{message=v;},async()=>{projectRef.current="FILMREAL"; return true;},"FILMPOC",projectRef,()=>{});
await changedDuringReload.reviewCreate();
assert.equal(checked,false,"a changed project cannot confirm an in-flight reload"); assert.equal(guard,true);
assert.match(source,/disabled=\{locked \|\| !project \|\| createUncertain\}/);
assert.match(source,/disabled=\{locked \|\| project !== createProject \|\| !createChecked\}/);
console.log("YouTrack uncertain film creation blocks retries and preserves the draft");
