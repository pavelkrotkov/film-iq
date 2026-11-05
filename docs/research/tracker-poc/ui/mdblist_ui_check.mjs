import assert from "node:assert/strict";
import { fetchRatings, safeSourceUrl } from "./mdblist_ui.js";

const rating = (source, kind, score, url) => ({
  source, source_name: source, kind, score_100: score, votes: 10, url,
});
let calls = 0;
const fake = async (url, options) => {
  calls++;
  assert.equal(url, "http://localhost:15177/ratings/42");
  assert.equal(options.credentials, "include");
  assert.equal(options.cache, "no-store");
  return { ok: true, json: async () => ({ tmdb_id: 42, ratings: [
    rating("tomatoes", "critic", 80, "https://www.rottentomatoes.com/m/fixture"),
    rating("popcorn", "audience", 90, "https://evil.test/forged"),
    rating("other", "unverified", null, null),
  ] }) };
};
assert.equal(calls, 0); // Constructing the helper makes no network request.
const rows = await fetchRatings(42, fake);
assert.equal(calls, 1);
assert.deepEqual(rows.map((row) => row.kind), ["critic", "audience", "unknown"]);
assert.equal(rows[0].url, "https://www.rottentomatoes.com/m/fixture");
assert.equal(rows[1].url, null);
assert.equal(rows[2].score_100, null);
assert.equal(safeSourceUrl("https://user:secret@www.imdb.com/", "imdb"), null);
assert.equal(safeSourceUrl("javascript:alert(1)", "imdb"), null);
assert.equal(safeSourceUrl("https://evil.test/imdb.com", "imdb"), null);
await assert.rejects(fetchRatings(42, async () => ({ ok: true, json: async () => ({ tmdb_id: 43, ratings: [] }) })), /identity/);
await assert.rejects(fetchRatings(42, async () => ({ ok: false, json: async () => ({ error: "MDBList returned HTTP 403" }) })), /HTTP 403/);
await assert.rejects(fetchRatings(42, async () => ({ ok: false, json: async () => ({ error: "secret provider response" }) })), /retry when ready/);
console.log("Synthetic MDBList opt-in, identity, scores, link, no-store and error checks passed");
