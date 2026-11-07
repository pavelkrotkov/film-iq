import assert from "node:assert/strict";
import {readFileSync} from "node:fs";

const source = readFileSync(new URL("./src.jsx", import.meta.url), "utf8");
const start = source.indexOf("  async function addFilm(event) {");
const end = source.indexOf("  async function addComment(event) {", start);
assert(start >= 0 && end > start, "Kaneo add handler must exist");
const reviewStart = source.indexOf("  async function reviewCreate() {", start);
assert(reviewStart > start && reviewStart < end, "Kaneo creation review handler must exist");
class CreatedFilmUnverified extends Error {}

async function run({uncertain = false, createFailure = false, refreshResult = true, loaded = true} = {}) {
  let creates = 0, title = "Fictional film", tmdb = "", error = "", guard = uncertain, checked = true, location = {hash:""};
  const createFilm = async () => { creates++; if (createFailure) throw new Error("Lost response"); return {id:"fixture-1"}; };
  const make = new Function("newTitle", "newTmdb", "project", "defaultState", "loaded", "createUncertain", "setBusy", "setError", "setCreateUncertain", "setCreateChecked", "identityField", "request", "createFilm", "setNewTitle", "setNewTmdb", "refresh", "location", "CreatedFilmUnverified", `${source.slice(start,end)}; return addFilm;`);
  const add = make(title,tmdb,"fixture-project","to-do",loaded,uncertain,()=>{},(v)=>{error=v;},(v)=>{guard=v;},(v)=>{checked=v;},async()=>"field",()=>{},createFilm,(v)=>{title=v;},(v)=>{tmdb=v;},async()=>refreshResult,location,CreatedFilmUnverified);
  await add({preventDefault() {}});
  return {creates, title, tmdb, error, guard, checked, location};
}

const blocked = await run({uncertain:true});
assert.equal(blocked.creates, 0); assert.equal(blocked.title, "Fictional film");
const failed = await run({createFailure:true});
assert.equal(failed.creates, 1); assert.equal(failed.guard, true); assert.equal(failed.checked, false);
assert.equal(failed.title, "Fictional film"); assert.match(failed.error, /may be incomplete/i);
const reloadFailed = await run({refreshResult:false});
assert.equal(reloadFailed.creates, 1); assert.equal(reloadFailed.guard, true); assert.equal(reloadFailed.checked, false);
assert.equal(reloadFailed.title, "Fictional film"); assert.match(reloadFailed.error, /created.*reload/i);
const unavailable = await run({loaded:false});
assert.equal(unavailable.creates, 0); assert.equal(unavailable.title, "Fictional film");
const success = await run();
assert.equal(success.creates, 1); assert.equal(success.title, ""); assert.equal(success.location.hash, "film=fixture-1");
let checked = false, guard = true, reloadWorks = false, message = "";
const makeReview = new Function("createChecked", "setCreateChecked", "setCreateUncertain", "setError", "refresh", `${source.slice(reviewStart, end)}; return {reviewCreate, allowCreateRetry};`);
const handlers = () => makeReview(checked, (v)=>{checked=v;}, (v)=>{guard=v;}, (v)=>{message=v;}, async()=>reloadWorks);
await handlers().reviewCreate(); handlers().allowCreateRetry();
assert.equal(checked, false); assert.equal(guard, true, "failed reload must not permit retry");
reloadWorks = true; await handlers().reviewCreate();
assert.equal(checked, true); assert.equal(guard, true, "successful reload still requires explicit confirmation");
assert.match(message, /check the film list/i); handlers().allowCreateRetry();
assert.equal(guard, false); assert.equal(checked, false);
assert.match(source, /disabled=\{busy \|\| !defaultState \|\| !loaded \|\| createUncertain\}/);
assert.match(source, /value=\{newTitle\}\s+disabled=\{busy\}\s+onChange=/, "new title cannot be replaced while creation is pending");
assert.match(source, /value=\{newTmdb\} disabled=\{busy\} onChange=/, "new ID cannot be replaced while creation is pending");
console.log("Kaneo uncertain film creation blocks retries and preserves the draft");
