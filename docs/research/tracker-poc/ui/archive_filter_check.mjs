import assert from "node:assert/strict";
import { filterFilms } from "./film_filters.js";
import { filterYoutrackFilms } from "./youtrack_filters.js";

const kaneo = [
  {id: "active", title: "Fictional active", status: "to-do", fields: {}},
  {id: "done", title: "Fictional done", status: "done", fields: {}},
  {id: "archived", title: "Fictional archived", status: "archived", fields: {}},
];
const k = (options = {}) => filterFilms(kaneo, {query: "", ...options}).map((film) => film.id);
assert.deepEqual(k(), ["active", "done"], "only archived records are hidden by default");
assert.deepEqual(k({showArchived: true}), ["active", "done", "archived"]);
assert.deepEqual(k({lifecycle: "archived"}), ["archived"], "explicit archived filter remains accessible");
assert.deepEqual(k({showArchived: true, lifecycle: "to-do"}), ["active"]);

const issue = (id, state) => ({idReadable: id, summary: `Fictional ${id}`, customFields: [{name: "FilmIQ Lifecycle", value: state ? {name: state} : null}]});
const youtrack = [issue("a", "Discovery"), issue("b", "Archived"), issue("c", null)];
const y = (options = {}) => filterYoutrackFilms(youtrack, {query: "", ...options}).map((film) => film.idReadable);
assert.deepEqual(y(), ["a", "c"], "unknown lifecycle is not inferred to be archived");
assert.deepEqual(y({showArchived: true}), ["a", "b", "c"]);
assert.deepEqual(y({stateFilter: "Archived"}), ["b"], "explicit archived filter remains accessible");
assert.deepEqual(y({showArchived: true, stateFilter: "Discovery"}), ["a"]);
console.log("Both discovery grids hide archived by default and allow explicit archive access");
