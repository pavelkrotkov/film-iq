import assert from "node:assert/strict";
import { build } from "esbuild";

let onLocationChange;
globalThis.YTApp = {register: async (callbacks) => {
  onLocationChange = callbacks.onAppLocationChange;
  return {fetchApp: async (path, options) => {
    assert.equal(path, "preferences/all");
    assert.deepEqual(options, {});
    return {preferences: {"FILMPOC-1": {recorded: true, preference: {interest_score: 8}}}};
  }};
}};
const bundle = await build({entryPoints: [new URL("./youtrack.jsx", import.meta.url).pathname], bundle: true, write: false, format: "esm", platform: "browser"});
const encoded = Buffer.from(bundle.outputFiles[0].contents).toString("base64");
const {providerObservation, providerDescription, providerFreshness, parseAppLocation, directReviews, previewMatchesFilm, readPreferences, submitOnEnter} = await import(`data:text/javascript;base64,${encoded}`);
assert.equal(typeof onLocationChange, "function");
assert.equal((await readPreferences())["FILMPOC-1"].interest_score, 8);
let submits = 0, prevented = 0;
const key = (tagName, extra = {}) => ({key:"Enter", target:{tagName}, preventDefault:() => prevented++, ...extra});
submitOnEnter(key("INPUT"), () => submits++);
submitOnEnter(key("TEXTAREA"), () => submits++);
submitOnEnter(key("INPUT", {nativeEvent:{isComposing:true}}), () => submits++);
assert.equal(submits, 1, "Enter submits an input without consuming textarea newlines or IME composition");
assert.equal(prevented, 1);
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
const link = {url:"https://example.com/review", provider:"Fixture Critic", type:"individual_critic_review", checked_at:"2026-11-05T12:00:00Z", identity_evidence:{input_title:"Fictional",source_page_title:"Fictional",source_directors:["Fictional Director"],source_year:2001,corroboration_urls:[],identity_caveat:"Source-supplied film identity not independently verified.",details_note:"Additional identity details are retained privately."}};
const reviewFilm = {customFields:[{name:"FilmIQ TMDB ID",value:42},{name:"FilmIQ Direct Review Links",value:{text:JSON.stringify({schema_version:1,tmdb_id:42,links:[link]})}}]};
assert.equal(directReviews(reviewFilm)[0].provider, "Fixture Critic");
assert.equal(directReviews({...reviewFilm,customFields:[{name:"FilmIQ TMDB ID",value:43},reviewFilm.customFields[1]]}),null);
assert.equal(previewMatchesFilm({issue_id:"FILMPOC-1",after:{}},"FILMPOC-1"),true);
assert.equal(previewMatchesFilm({issue_id:"FILMPOC-1",after:{}},"FILMPOC-2"),false);
assert.equal(previewMatchesFilm({issue_id:"FILMPOC-1"},"FILMPOC-1"),false);
console.log("YouTrack route parsing and synthetic provider unknown/partial/freshness checks passed");
