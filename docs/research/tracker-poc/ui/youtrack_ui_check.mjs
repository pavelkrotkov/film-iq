import assert from "node:assert/strict";
import { build } from "esbuild";
import { filmYearLabel, filterYoutrackFilms, localWatchlistLabel } from "./youtrack_filters.js";

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
assert.equal(providerDescription(complete, "buy"), "Unknown", "older synthetic fixtures do not report purchases");
const syntheticPurchase = providerObservation(film({...fixture, buy: ["Fixture Purchase"]}));
assert.equal(providerDescription(syntheticPurchase, "buy"), "Fixture Purchase");
assert.equal(providerDescription(syntheticPurchase, "free"), "Unknown");
const liveOffers = providerObservation({live:{availability:{status:"complete",checked_at:"2026-11-05T00:00:00Z",offers:[
  {provider:"Fixture Stream",kind:"subscription"},{provider:"Fixture Rent",kind:"rent"},
  {provider:"Fixture Buy",kind:"buy"},{provider:"Fixture Free",kind:"free"},{provider:"Fixture Ads",kind:"ads"},
]}}});
assert.equal(providerDescription(liveOffers, "buy"), "Fixture Buy");
assert.equal(providerDescription(liveOffers, "free"), "Fixture Free");
assert.equal(providerDescription(liveOffers, "ads"), "Fixture Ads");
const noLiveOffers = providerObservation({live:{availability:{status:"complete",offers:[]}}});
assert.equal(providerDescription(noLiveOffers, "buy"), "None reported");
const partialLiveOffers = providerObservation({live:{availability:{status:"partial",offers:[]}}});
assert.equal(providerDescription(partialLiveOffers, "buy"), "Unknown (partial response)");
const availabilityFilm = {idReadable:"FILMPOC-1", customFields:[], live:{availability:{status:"complete",offers:[
  {provider:"Fixture Buy",kind:"buy"}, {provider:"Fixture Stream",kind:"subscription"},
]}}};
assert.equal(filterYoutrackFilms([availabilityFilm], {provider:"Fixture Buy"}).length, 0, "purchase providers are not subscription matches");
assert.equal(filterYoutrackFilms([availabilityFilm], {provider:"Fixture Stream"}).length, 1);
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
const sourceEvidence = JSON.stringify({tmdb_id:42,status:"available",links:[{url:"https://example.invalid/film",entry_id:"entry",revision_id:"revision"}]});
const years = (release, source, id = 42, evidence = sourceEvidence) => ({customFields:[{name:"FilmIQ Release Year",value:release},{name:"FilmIQ Source Year",value:source},{name:"FilmIQ TMDB ID",value:id},{name:"FilmIQ Source Evidence",value:{text:evidence}}]});
assert.equal(filmYearLabel(years(2001, 2002)), "Stored release year 2001 · Source-listed year 2002 (source field; verify identity and edits)");
assert.equal(filmYearLabel(years(2001, null)), "Stored release year 2001");
assert.equal(filmYearLabel(years(null, 2002)), "Source-listed year 2002 (source field; verify identity and edits)");
assert.equal(filmYearLabel(years(null, null), 2003), "TMDB-supplied year 2003");
assert.equal(filmYearLabel(years(null, null)), "Year unknown");
assert.equal(filmYearLabel(years("2001", 0)), "Year unknown");
assert.equal(filmYearLabel(years(null, 2002, 43), 2003), "TMDB-supplied year 2003", "changed identity must not hide valid live year");
assert.equal(filmYearLabel(years(2001, 2002, 43)), "Stored release year 2001", "changed identity must not hide stored release year");
assert.equal(filmYearLabel(years(null, 2002, 43)), "Year unknown");
assert.equal(filmYearLabel(years(null, 2002, 42, "invalid")), "Year unknown");
assert.equal(localWatchlistLabel(null, "FILMPOC-1"), "Local watchlist unavailable");
assert.equal(localWatchlistLabel({}, "FILMPOC-1"), "Local watchlist unknown");
assert.equal(localWatchlistLabel({"FILMPOC-1":{watchlist:null}}, "FILMPOC-1"), "Local watchlist unknown");
assert.equal(localWatchlistLabel({"FILMPOC-1":{watchlist:true}}, "FILMPOC-1"), "On local watchlist");
assert.equal(localWatchlistLabel({"FILMPOC-1":{watchlist:false}}, "FILMPOC-1"), "Not on local watchlist");
assert.equal(localWatchlistLabel({"FILMPOC-1":{watchlist:0}}, "FILMPOC-1"), "Local watchlist unknown");
console.log("YouTrack route parsing and synthetic provider unknown/partial/freshness checks passed");
