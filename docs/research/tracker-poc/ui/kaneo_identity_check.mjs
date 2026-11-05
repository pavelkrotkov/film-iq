import assert from "node:assert/strict";
import { createFilm, CreatedFilmUnverified, identityField, matchedLive } from "./kaneo_identity.js";
import { chooseBatch, mergeResult } from "./live_batch.js";
import { filterFilms } from "./film_filters.js";

const film = {id: "fictional", title: "A Film", fields: {"POC TMDB ID": "42"}};
const data = {tmdb_id: 42, title: "A Film", availability: {status: "complete", offers: [{kind: "subscription", provider: "Example"}]}};
assert.equal(matchedLive(film, {data}), data);
const alternate = {...data, title: "Localized title", original_title: " A\t FILM "};
assert.equal(matchedLive(film, {data: alternate}), alternate, "the exact original title can match");
assert.equal(matchedLive({...film, title: "Edited title"}, {data: alternate}), null, "edited titles remain withheld");
assert.equal(matchedLive({...film, fields: {"POC TMDB ID": "43"}}, {data: alternate}), null, "an original-title match cannot cross IDs");
assert.equal(matchedLive(film, {data: {...alternate, original_title: ["A Film"]}}), null, "invalid original title stays withheld");
assert.equal(matchedLive(film, {data: {...alternate, title: null}}), null, "a missing returned title stays withheld");
assert.equal(matchedLive({...film, title: "Another Film"}, {data}), null, "title edit hides the old live metadata");
assert.equal(matchedLive(film, {data: {...data, title: "Another Film"}}), null, "initial mismatch stays hidden");
assert.equal(matchedLive({...film, fields: {"POC TMDB ID": "43"}}, {data}), null, "ID change hides old metadata");
const mismatched = {...film, live: matchedLive(film, {data: {...data, title: "Another Film"}})};
assert.equal(filterFilms([mismatched], {query: "", provider: "Example"}).length, 0, "mismatched providers cannot match the filter");
assert.equal(chooseBatch([{...film, fields: {"POC TMDB ID": "43"}}], {[film.id]: {data}}).length, 1, "an edited ID becomes eligible for a fresh request");
assert.equal(mergeResult({data}, {data: {...data, tmdb_id: 43, availability: {status: "unknown", offers: []}}}).data.availability.status, "unknown", "old providers cannot cross identities");

const calls = [];
const request = async (path) => {
  calls.push(path);
  return path.endsWith("/values") ? [{fieldId: "field", taskId: "other", value: "42"}] : [{id: "field", name: "POC TMDB ID", type: "text"}];
};
assert.equal(await identityField(request, "fictional-project", "43"), "field");
await assert.rejects(() => identityField(request, "fictional-project", "42"), /already belongs/);
assert.equal(await identityField(request, "fictional-project", "42", "other"), "field");
await assert.rejects(() => identityField(request, "fictional-project", "0"), /positive integer/);
await assert.rejects(() => identityField(async () => [], "fictional-project", "43"), /exactly one/);
await assert.rejects(() => identityField(async () => [{name: "POC TMDB ID", type: "text"}, {name: "POC TMDB ID", type: "number"}], "fictional-project", "43"), /exactly one/);
assert.ok(calls.every((path) => path.includes("fictional-project")));
const payload = {title: "Fictional film", customFields: [{fieldId: "field", value: "43"}]};
const createdCalls = [];
const createRequest = async (path, method, body) => {
  createdCalls.push({path, method, body});
  return method === "POST" ? {id: "fictional-task"} : [{fieldId: "field", value: "43"}];
};
assert.deepEqual(await createFilm(createRequest, "fictional-project", payload, "field", "43"), {id: "fictional-task"});
assert.deepEqual(createdCalls, [
  {path: "/task/fictional-project", method: "POST", body: payload},
  {path: "/custom-field/task/fictional-task", method: undefined, body: undefined},
]);
for (const readback of [[], [{fieldId: "field", value: "wrong"}], new Error("unavailable")]) {
  const fake = async (_path, method) => {
    if (method === "POST") return {id: "fictional-task"};
    if (readback instanceof Error) throw readback;
    return readback;
  };
  await assert.rejects(() => createFilm(fake, "fictional-project", payload, "field", "43"), (error) => error instanceof CreatedFilmUnverified && /fictional-task.*created.*could not be confirmed/i.test(error.message));
}
console.log("Kaneo fictional identity and live metadata checks passed");
