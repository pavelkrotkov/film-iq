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
// The separate preference workflow intentionally edits fixture 0001. Check
// the whole live result rather than assuming that synthetic state is pristine.
const expected = (preferences) => data.films
  .filter((film) => {
    const raw = film.fields["POC Subscription Providers"] || film.fields["POC Streaming"];
    const hasNetflix = raw && JSON.parse(raw).includes("Netflix");
    return hasNetflix && (preferences[film.id]?.interest_score ?? 0) >= 8;
  })
  .map((film) => film.fields["POC Fixture ID"])
  .sort();
assert.deepEqual(ids(data.userA), expected(data.userA));
assert.deepEqual(ids(data.userB), expected(data.userB));
assert.ok(ids(data.userA).includes("fixture-0008"));
assert.ok(ids(data.userB).includes("fixture-0004"));
const ordered = filterFilms(data.films, {
  ...options,
  provider: "",
  minimum: "",
});
assert.equal(data.userA[ordered[0].id].interest_score, 10);
console.log(
  `Live Kaneo field and preference joins passed for ${data.films.length} films and both users`,
);
