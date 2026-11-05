import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { filterFilms } from "./film_filters.js";

const data = JSON.parse(readFileSync(0, "utf8"));
const options = {
  query: "",
  provider: "Netflix",
  watchlistOnly: false,
  minimum: "8",
  genre: "",
  lifecycle: "",
  watched: "",
  freshnessFilter: "",
  sortInterest: true,
  preferences: data.userA,
};
const ids = (preferences) =>
  filterFilms(data.films, { ...options, preferences })
    .map((f) => f.fields["POC Fixture ID"])
    .sort();
assert.deepEqual(ids(data.userA), ["fixture-0008", "fixture-0028"]);
assert.deepEqual(ids(data.userB), [
  "fixture-0004",
  "fixture-0016",
  "fixture-0024",
]);
const ordered = filterFilms(data.films, {
  ...options,
  provider: "",
  minimum: "",
});
assert.equal(data.userA[ordered[0].id].interest_score, 10);
console.log(
  `Live Kaneo field and preference joins passed for ${data.films.length} films and both users`,
);
