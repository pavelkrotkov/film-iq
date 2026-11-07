import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { build } from "esbuild";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";

const require = createRequire(import.meta.url);
const built = await build({
  entryPoints: [new URL("./identity_review.jsx", import.meta.url).pathname],
  bundle: true, format: "cjs", platform: "node", external: ["react"], write: false,
});
const module = {exports: {}};
new Function("require", "module", "exports", built.outputFiles[0].text)(require, module, module.exports);
const { IdentityReview } = module.exports;
const data = {
  tmdb_id: 42, title: "Fictional response", original_title: "Alternate fictional title",
  year: 2001, directors: ["Fictional Director"],
  imdb_title_url: "https://www.imdb.com/title/tt1234567/",
  poster_url: "https://image.tmdb.org/t/p/w500/fixture.jpg",
  availability: {status: "complete", offers: [{provider: "Fictional Stream", kind: "subscription"}]},
};
const render = (props) => renderToStaticMarkup(React.createElement(IdentityReview, props));
const props = {expectedId: 42, savedTitle: "Fictional saved title", sourceYear: "2002", sourceDirector: "Source Director", data};
const reviewedLink = {
  url: "https://review.example.test/film", provider: "Fictional review", type: "individual_critic_review", checked_at: "2026-11-06",
  identity_evidence: {input_title: "Fictional saved title", source_page_title: "Fictional response", source_directors: ["Source Director"], source_year: 2002, corroboration_urls: [], identity_caveat: "Source-supplied film identity not independently verified.", details_note: "Additional identity details are retained privately."},
};
const reviewEvidence = JSON.stringify({schema_version: 1, tmdb_id: 42, links: [reviewedLink]});
const mismatch = render(props);
for (const value of ["Film identity needs review", "Fictional saved title", "2002", "Source Director", "Fictional response", "Alternate fictional title", "2001", "Fictional Director", "do not confirm a match"]) assert.ok(mismatch.includes(value), `missing ${value}`);
assert.match(mismatch, /Artwork and streaming offers are withheld/);
assert.match(mismatch, /Open candidate IMDb title page/);
assert.match(mismatch, /IMDb ID supplied by TMDB; the film match is not independently verified/);
assert.match(mismatch, /href="https:\/\/www\.imdb\.com\/title\/tt1234567\/"/);
assert.match(mismatch, /rel="noreferrer"/);
assert.doesNotMatch(mismatch, /Fictional Stream|fixture\.jpg|<img/i, "unverified offers and artwork must not render");
const withReview = render({...props, reviewEvidence});
assert.match(withReview, /Existing review evidence uses a matching provider title/);
assert.match(withReview, /unverified identity lead, not a confirmed film match/);
assert.match(withReview, /href="https:\/\/review\.example\.test\/film"/);
assert.doesNotMatch(withReview, /Fictional Stream|fixture\.jpg|<img/i, "matching review evidence must not reveal offers or artwork");
assert.match(render({...props, reviewEvidence: JSON.stringify({schema_version: 1, tmdb_id: 42, links: [{...reviewedLink, identity_evidence: {...reviewedLink.identity_evidence, source_page_title: "alternate FICTIONAL TITLE"}}]})}), /Existing review evidence uses a matching provider title/, "original provider title is matched with normalization");
for (const invalid of [
  JSON.stringify({schema_version: 1, tmdb_id: 43, links: [reviewedLink]}),
  JSON.stringify({schema_version: 1, tmdb_id: 42, links: [{...reviewedLink, url: "javascript:alert(1)"}]}),
  JSON.stringify({schema_version: 1, tmdb_id: 42, links: [{...reviewedLink, identity_evidence: {...reviewedLink.identity_evidence, input_title: "A different saved title"}}]}),
  JSON.stringify({schema_version: 1, tmdb_id: 42, links: [{...reviewedLink, identity_evidence: {...reviewedLink.identity_evidence, source_page_title: "A different source title"}}]}),
  "not-json", null,
]) assert.doesNotMatch(render({...props, reviewEvidence: invalid}), /Existing review evidence uses a matching provider title/, "invalid or unmatched evidence remains hidden");
assert.doesNotMatch(render({...props, provider: "Fictional cache", reviewEvidence}), /Existing review evidence uses a matching provider title/, "fixture data must not expose real evidence");
assert.doesNotMatch(render({...props, provider: "Fictional cache"}), /IMDb title page/, "fixture data must not expose a live link");
for (const unsafe of ["https://imdb.com/title/tt1234567/", "https://www.imdb.com/title/tt1234567/?ref=unsafe", "javascript:alert(1)", null]) {
  assert.doesNotMatch(render({...props, data: {...data, imdb_title_url: unsafe}}), /IMDb title page/, "invalid URLs remain unavailable");
}
assert.equal(render({...props, savedTitle: "  FICTIONAL RESPONSE  "}), "", "matching title uses the normal view");
assert.equal(render({...props, savedTitle: "alternate fictional title"}), "", "matching original title uses the normal view");
assert.equal(render({...props, expectedId: 43}), "", "old metadata is not displayed for a changed ID");
assert.equal(render({...props, data: null}), "", "no response produces no comparison");
const unknown = render({...props, sourceYear: null, sourceDirector: null, data: {...data, original_title: null, year: null, directors: null}});
assert.equal((unknown.match(/Unknown/g) || []).length, 5, "missing values remain unknown");
const escaped = render({...props, savedTitle: "<script>fictional</script>"});
assert.doesNotMatch(escaped, /<script>/, "user-supplied title remains escaped");
console.log("Fictional identity-review display, matching guard and withheld data checks passed");
