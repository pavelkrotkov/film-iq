import assert from "node:assert/strict";
import { filterYoutrackFilms, localWatchLabel, localWatchStatus } from "./youtrack_filters.js";

const films = [1, 2, 3, 4].map((id) => ({idReadable: `FILMPOC-${id}`, summary: `Fictional ${id}`, customFields: [{name:"FilmIQ TMDB ID",value:id}]}));
const preferences = {
  "FILMPOC-1": {watched_at: "2026-01-01T12:00:00.000Z"},
  "FILMPOC-2": {watched_at: null},
  "FILMPOC-4": {watched_at: "invalid"},
};
const original = structuredClone(preferences);
const options = {preferences, query: "", localWatched: "", movary: {status: "available", films: {"FILMPOC-2": {watched: true,tmdb_id:2}}}};
const ids = (value) => filterYoutrackFilms(films, value).map((film) => film.idReadable);
assert.equal(localWatchStatus(preferences, "FILMPOC-1"), "watched");
assert.equal(localWatchStatus(preferences, "FILMPOC-2"), "not_recorded");
assert.equal(localWatchStatus(preferences, "FILMPOC-3"), "unknown");
assert.equal(localWatchStatus(preferences, "FILMPOC-4"), "unknown");
assert.equal(localWatchLabel(preferences, "FILMPOC-2"), "No watched timestamp recorded");
assert.equal(localWatchLabel(preferences, "FILMPOC-3"), "Unknown");
assert.equal(localWatchLabel(null, "FILMPOC-1"), "Unavailable");
assert.deepEqual(ids({...options, localWatched: "watched"}), ["FILMPOC-1"]);
assert.deepEqual(ids({...options, localWatched: "not_recorded"}), ["FILMPOC-2"]);
assert.deepEqual(ids({...options, localWatched: "unknown"}), ["FILMPOC-3", "FILMPOC-4"]);
assert.deepEqual(ids({...options, preferences: null, localWatched: "unknown"}), [], "an unavailable preference source must not be treated as unknown for every film");
assert.deepEqual(ids({...options, movaryOnly: true}), ["FILMPOC-2"]);
const editedId = films.map((film) => film.idReadable === "FILMPOC-2" ? {...film,customFields:[{name:"FilmIQ TMDB ID",value:42}]} : film);
assert.deepEqual(filterYoutrackFilms(editedId,{...options,movaryOnly:true}), [], "a changed identity cannot inherit old watched status");
assert.ok(filterYoutrackFilms(editedId,{...options,excludeMovaryWatched:true}).some((film) => film.idReadable === "FILMPOC-2"), "unknown watched status remains visible when excluding known watched films");
assert.deepEqual(ids({...options,movary:{status:"available",films:{"FILMPOC-2":{watched:true}}},movaryOnly:true}), [], "legacy entries without IDs are unknown");
assert.deepEqual(ids({...options,movary:{status:"available",films:{"FILMPOC-2":{watched:true,tmdb_id:null}}},movaryOnly:true}), [], "unbound entries are unknown");
assert.ok(ids({...options,movary:{status:"available",films:{"FILMPOC-2":{watched:true,tmdb_id:null}}},excludeMovaryWatched:true}).includes("FILMPOC-2"), "unbound evidence does not exclude the film as watched");
assert.deepEqual(ids({...options, movaryOnly: true, localWatched: "watched"}), [], "Movary and local watched markers are independent");
assert.deepEqual(preferences, original, "filters must not change saved preferences");
console.log("YouTrack local watched filters preserve unknowns and keep Movary separate");
