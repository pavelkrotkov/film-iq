import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { build } from "esbuild";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";

const require = createRequire(import.meta.url);
const built = await build({
  entryPoints: [new URL("./review_identity.jsx", import.meta.url).pathname],
  bundle: true, format: "cjs", platform: "node", external: ["react"], write: false,
});
const module = {exports: {}};
new Function("require", "module", "exports", built.outputFiles[0].text)(require, module, module.exports);
const evidence = {input_title: "Fictional source", source_page_title: "Fictional page", source_directors: ["Fictional Director"], source_year: 2001, identity_caveat: "Identity unverified.", details_note: "Details private."};
const render = (value) => renderToStaticMarkup(React.createElement(module.exports.ReviewIdentity, {evidence: value}));
const known = render(evidence);
for (const value of ["Fictional source", "Fictional page", "Fictional Director", "2001", "Identity unverified."]) assert.ok(known.includes(value));
assert.match(render({...evidence, source_year: null}), /Source year unknown/);
assert.doesNotMatch(render({...evidence, input_title: "<script>fixture</script>"}), /<script>/);
console.log("Shared fictional review identity evidence renders with unknown-year handling");
