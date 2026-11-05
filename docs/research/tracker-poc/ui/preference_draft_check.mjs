import assert from "node:assert/strict";
import { emptyPreference, markPreferenceSaved, mergeFilmDraft, syncPreferenceDraft } from "./preference_draft.js";

const original = { title: "Saved title", description: "Saved synopsis", status: "to-do", tmdb: "42", year: "2001", genre: "Drama" };
const editing = { title: "Edited title", description: "Unfinished synopsis", status: "in-progress", tmdb: "43", year: "2002", genre: "Comedy" };
assert.equal(mergeFilmDraft(editing, original, true), editing, "refresh must retain unsaved title, synopsis and state");
assert.deepEqual(mergeFilmDraft(editing, original, false), original, "clean fields should refresh");
const saved = { ...emptyPreference, interest_score: 6 };
const changed = { ...saved, personal_notes: "Unfinished notes" };
let draft = { filmId: "a", value: changed, dirty: true };
assert.equal(syncPreferenceDraft(draft, "a", {a: saved}), draft, "unrelated film refresh must preserve preferences");
assert.equal(syncPreferenceDraft(draft, "a", null), draft, "failed preference fetch must not erase the draft");
assert.equal(markPreferenceSaved(draft, "a", saved), draft, "a later edit must survive an earlier save");
draft = markPreferenceSaved(draft, "a", changed);
assert.equal(syncPreferenceDraft(draft, "a", {a: saved}).value, saved, "successful save reloads stored preferences");
assert.equal(syncPreferenceDraft(draft, "b", {b: saved}).value, saved, "another film gets its own preferences");
console.log("Kaneo film and preference drafts survive unrelated refreshes");
