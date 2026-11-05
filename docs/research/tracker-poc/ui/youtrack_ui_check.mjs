import assert from "node:assert/strict";
import { build } from "esbuild";

let onLocationChange;
globalThis.YTApp = {register: async (callbacks) => { onLocationChange = callbacks.onAppLocationChange; return {}; }};
const bundle = await build({entryPoints: [new URL("./youtrack.jsx", import.meta.url).pathname], bundle: true, write: false, format: "esm", platform: "browser"});
const encoded = Buffer.from(bundle.outputFiles[0].contents).toString("base64");
const {providerObservation, providerDescription, providerFreshness, parseAppLocation} = await import(`data:text/javascript;base64,${encoded}`);
assert.equal(typeof onLocationChange, "function");
assert.deepEqual(parseAppLocation({search: "project=FILMPOC&film=FILMPOC-12"}), {project: "FILMPOC", film: "FILMPOC-12"});
assert.deepEqual(parseAppLocation({search: "project=FILMPOC&film=FILMREAL-12"}), {project: "FILMPOC", film: null});
assert.deepEqual(parseAppLocation({search: "project=OTHER&film=OTHER-1"}), {project: "FILMREAL", film: null});

const film = (value) => ({customFields: [{name: "FilmIQ Provider Observation", value: {text: JSON.stringify(value)}}]});
const fixture = {source: "synthetic fixture, not TMDB", subscription: ["Fixture Stream"], rent: [], checked_at: "2026-11-05T00:00:00Z"};
const complete = providerObservation(film(fixture));
assert.equal(providerDescription(complete, "subscription"), "Fixture Stream");
assert.equal(providerDescription(complete, "rent"), "None reported");
assert.equal(providerFreshness(complete, Date.parse("2026-11-06T00:00:00Z")), "recent");
assert.equal(providerFreshness(complete, Date.parse("2026-11-20T00:00:00Z")), "stale");
const partial = providerObservation(film({...fixture, status: "partial", subscription: []}));
assert.equal(providerDescription(partial, "subscription"), "Unknown (partial response)");
assert.equal(providerDescription(providerObservation(film({...fixture, status: "unknown"})), "subscription"), "Unknown");
assert.equal(providerDescription(providerObservation(film({...fixture, source: "unreviewed source"})), "rent"), "Unknown");
assert.equal(providerDescription(providerObservation(film({...fixture, subscription: [null]})), "rent"), "Unknown");
console.log("YouTrack route parsing and synthetic provider unknown/partial/freshness checks passed");
