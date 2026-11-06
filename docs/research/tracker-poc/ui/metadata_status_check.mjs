import assert from "node:assert/strict";
import {createRequire} from "node:module";
import {readFile} from "node:fs/promises";
import {build} from "esbuild";
import React from "react";
import {renderToStaticMarkup} from "react-dom/server";
import {expireCachedResults} from "./live_batch.js";

const require = createRequire(import.meta.url);
const built = await build({entryPoints: [new URL("./metadata_status.jsx", import.meta.url).pathname], bundle: true, format: "cjs", platform: "node", external: ["react"], write: false});
const module = {exports: {}};
new Function("require", "module", "exports", built.outputFiles[0].text)(require, module, module.exports);
const render = (cached) => renderToStaticMarkup(React.createElement(module.exports.MetadataUnavailable, {cached}));
const fictional = {data: {cache_expires_at: "2030-01-01T00:00:00Z", synopsis: "Fictional source synopsis"}};
const expired = expireCachedResults({film: fictional}, Date.parse(fictional.data.cache_expires_at));
assert.equal(expired.results.film, undefined);
assert.match(render(true), /unknown.*may not have been loaded.*unavailable.*may have expired/);
assert.match(render(true), /synopsis field below is stored separately/);
assert.doesNotMatch(render(false), /expired/);
for (const filename of ["src.jsx", "youtrack.jsx"]) {
  const source = await readFile(new URL(filename, import.meta.url), "utf8");
  assert.match(source, /<MetadataUnavailable cached=\{liveCache \|\| cacheFixture\} \/>/);
  assert.match(source, /TMDB synopsis unknown\./);
  await build({entryPoints: [new URL(filename, import.meta.url).pathname], bundle: true, format: "esm", write: false});
}
console.log("Fictional metadata expiry and unknown-synopsis presentation passed for both UIs");
