import assert from "node:assert/strict";
import { handleExternalRoute, hasUnsavedPageDraft, routeLocation } from "./youtrack_navigation.js";

const clean = {filmDirty:false, prefDirty:false, commentDrafts:{}, newTitle:"", newTmdbId:""};
assert.equal(hasUnsavedPageDraft(clean), false);
assert.equal(hasUnsavedPageDraft({...clean, filmDirty:true}), true);
assert.equal(hasUnsavedPageDraft({...clean, prefDirty:true}), true);
assert.equal(hasUnsavedPageDraft({...clean, commentDrafts:{"FILMPOC-1":"unsent"}}), true);
assert.equal(hasUnsavedPageDraft({...clean, commentDrafts:{"FILMPOC-1":"  "}}), false);
assert.equal(hasUnsavedPageDraft({...clean, newTitle:"Fictional"}), true);
assert.equal(hasUnsavedPageDraft({...clean, newTmdbId:"42"}), true);

const current = {project: "FILMPOC", film: "FILMPOC-1"};
const next = {project: "FILMPOC", film: "FILMPOC-2"};
const events = [];
const callbacks = {
  apply: (value) => events.push(["apply", value]),
  queue: (value) => events.push(["queue", value]),
  restore: async (value) => events.push(["restore", value]),
  notify: (value) => events.push(["notify", value]),
};
await handleExternalRoute(current, next, {}, callbacks);
assert.deepEqual(events.splice(0), [["apply", next]]);
await handleExternalRoute(current, next, {filmDirty: true}, callbacks);
assert.deepEqual(events.splice(0), [["queue", next], ["restore", current]]);
await handleExternalRoute(current, next, {prefDirty: true}, callbacks);
assert.deepEqual(events.splice(0), [["queue", next], ["restore", current]]);
await handleExternalRoute(current, next, {pendingPreview: {}}, callbacks);
assert.equal(events.some(([kind]) => kind === "queue" || kind === "apply"), false);
assert.equal(events.filter(([kind]) => kind === "restore").length, 1);
assert.match(events.find(([kind]) => kind === "notify")[1], /preview/i);
events.length = 0;
await handleExternalRoute(current, current, {filmDirty: true, pendingPreview: {}}, callbacks);
assert.deepEqual(events, [], "restoration callback for the same screen must not loop");
await handleExternalRoute(current, next, {pendingNavigation: {}, busy: true}, callbacks);
assert.equal(events.some(([kind]) => kind === "queue" || kind === "apply"), false);
events.length = 0;
await handleExternalRoute(current, next, {filmDirty: true}, {...callbacks, restore: async () => {throw new Error("synthetic failure");}});
assert.equal(events.some(([kind]) => kind === "apply"), false, "failed restoration must keep the draft screen");
assert.equal(events.some(([kind]) => kind === "queue"), true);
assert.match(events.find(([kind]) => kind === "notify")[1], /could not restore/i);
assert.deepEqual(routeLocation(current), {search: "project=FILMPOC&film=FILMPOC-1"});
assert.deepEqual(routeLocation({project: "FILMREAL", film: null}), {search: "project=FILMREAL"});
console.log("YouTrack synthetic external navigation guards and restoration checks passed");
