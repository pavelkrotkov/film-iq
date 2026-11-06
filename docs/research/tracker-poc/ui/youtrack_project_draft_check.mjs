import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {hasNewFilmDraft} from "./youtrack_navigation.js";

// Exercise the actual picker/route handlers without a browser or tracker.
const source = readFileSync(new URL("./youtrack.jsx", import.meta.url), "utf8");
const start = source.indexOf("  async function navigateRoute(next) {");
const end = source.indexOf("  const shownFilms =", start);
assert.ok(start >= 0 && end > start);
const make = new Function("markFilmDirty", "markPrefDirty", "setNewFilmTitle", "setNewFilmTmdbId", "projectRef", "selectedRef", "setProject", "setSelected", "host", "routeLocation", "setError", "pendingPreview", "pendingNavigation", "filmDirty", "prefDirty", "hasNewFilmDraft", "guardsRef", "setQueued", `${source.slice(start, end)}; return {navigateRoute,selectProject};`);

for (const draft of [{newTitle:"Fictional film",newTmdbId:""}, {newTitle:"",newTmdbId:"123"}]) {
  const values = {...draft}, projectRef = {current:"FILMPOC"}, selectedRef = {current:null};
  const guardsRef = {current:values};
  const routed = [], queued = [];
  const handlers = make(() => {}, () => {}, (value) => {values.newTitle=value;}, (value) => {values.newTmdbId=value;}, projectRef, selectedRef, () => {}, () => {}, {navigation:{updateAppLocation:async (value) => routed.push(value)}}, (value) => value, () => {}, null, null, false, false, hasNewFilmDraft, guardsRef, (value) => queued.push(value));
  await handlers.selectProject("FILMREAL");
  assert.deepEqual(queued, [{kind:"project",value:"FILMREAL"}]);
  assert.deepEqual(values, draft, "cancel or waiting retains both draft fields");
  assert.equal(routed.length, 0);
  await handlers.navigateRoute({project:"FILMPOC",film:"FILMPOC-1"});
  assert.deepEqual(values, draft, "same-project navigation retains the new-film draft");
  await handlers.selectProject("FILMREAL", true);
  assert.deepEqual(values, {newTitle:"",newTmdbId:""}, "explicit discard clears the draft");
  assert.equal(projectRef.current, "FILMREAL");
}
console.log("YouTrack new-film drafts require explicit discard before changing projects");
