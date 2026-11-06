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
  poster_url: "https://image.tmdb.org/t/p/w500/fixture.jpg",
  availability: {status: "complete", offers: [{provider: "Fictional Stream", kind: "subscription"}]},
};
const render = (props) => renderToStaticMarkup(React.createElement(IdentityReview, props));
const props = {expectedId: 42, savedTitle: "Fictional saved title", sourceYear: "2002", sourceDirector: "Source Director", data};
const mismatch = render(props);
for (const value of ["Film identity needs review", "Fictional saved title", "2002", "Source Director", "Fictional response", "Alternate fictional title", "2001", "Fictional Director", "do not confirm a match"]) assert.ok(mismatch.includes(value), `missing ${value}`);
assert.match(mismatch, /Artwork and streaming offers are withheld/);
assert.doesNotMatch(mismatch, /Fictional Stream|fixture\.jpg|<img/i, "unverified offers and artwork must not render");
assert.equal(render({...props, savedTitle: "  FICTIONAL RESPONSE  "}), "", "matching title uses the normal view");
assert.equal(render({...props, savedTitle: "alternate fictional title"}), "", "matching original title uses the normal view");
assert.equal(render({...props, expectedId: 43}), "", "old metadata is not displayed for a changed ID");
assert.equal(render({...props, data: null}), "", "no response produces no comparison");
const unknown = render({...props, sourceYear: null, sourceDirector: null, data: {...data, original_title: null, year: null, directors: null}});
assert.equal((unknown.match(/Unknown/g) || []).length, 5, "missing values remain unknown");
const escaped = render({...props, savedTitle: "<script>fictional</script>"});
assert.doesNotMatch(escaped, /<script>/, "user-supplied title remains escaped");
console.log("Fictional identity-review display, matching guard and withheld data checks passed");
