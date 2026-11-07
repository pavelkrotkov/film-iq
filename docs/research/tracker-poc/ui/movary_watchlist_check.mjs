import assert from "node:assert/strict";
import {createRequire} from "node:module";
import {build} from "esbuild";
import React from "react";
import {renderToStaticMarkup} from "react-dom/server";
import {filterFilms} from "./film_filters.js";
import {filterYoutrackFilms} from "./youtrack_filters.js";

const require = createRequire(import.meta.url);
const built = await build({entryPoints:[new URL("./movary_watchlist.jsx", import.meta.url).pathname], bundle:true, format:"cjs", platform:"node", external:["react"], write:false});
const module = {exports:{}};
new Function("require", "module", "exports", built.outputFiles[0].text)(require, module, module.exports);
const {MovaryWatchlist, MovaryWatchlistBadge, observedWatchlistKeys, reconcileMovaryWatchlist, watchlistForProject} = module.exports;
const snapshot = {status:"available", source:"Movary", observed_at:"2026-11-06T12:00:00Z", entries:[
  {tmdb_id:42,title:"Fictional existing",added_at:"2026-11-01 09:02:03"},
  {tmdb_id:43,title:"Fictional missing",added_at:null},
  {tmdb_id:44,title:null,added_at:null},
]};
const films = [{id:"one", tmdb:42, title:"Fictional existing"}];
const getId = (film) => film.tmdb, getKey = (film) => film.id, getTitle = (film) => film.title;
const rows = reconcileMovaryWatchlist(snapshot, films, getId);
assert.equal(rows[0].film.id, "one");
assert.equal(rows[1].film, null);
assert.equal(rows[2].entry.title, null);
assert.equal(reconcileMovaryWatchlist({status:"unknown"}, films, getId), null);
assert.equal(reconcileMovaryWatchlist({...snapshot,entries:[...snapshot.entries,snapshot.entries[0]]}, films, getId), null);
assert.equal(reconcileMovaryWatchlist({...snapshot,entries:[{tmdb_id:0,title:"bad",added_at:null}]}, films, getId), null);
assert.equal(reconcileMovaryWatchlist({...snapshot,entries:[{tmdb_id:42,title:"bad",added_at:{}}]}, films, getId), null);
const ambiguous = reconcileMovaryWatchlist(snapshot, [...films, {id:"two",tmdb:42}], getId);
assert.equal(ambiguous[0].film, null); assert.equal(ambiguous[0].ambiguous, true);
assert.equal(watchlistForProject({project:"fictional-a",snapshot}, "fictional-a"), snapshot);
assert.equal(watchlistForProject({project:"fictional-a",snapshot}, "fictional-b"), null);
assert.equal(watchlistForProject({project:"fictional-a",snapshot}, null), null);

// The source watchlist can be combined with grid filters independently of
// the local POC watchlist; duplicate tracker IDs and missing entries stay out.
const source = {...snapshot, entries:[42,43,44,45].map((tmdb_id) => ({tmdb_id,title:`Fictional ${tmdb_id}`,added_at:null}))};
const availability = {status:"complete",checked_at:new Date().toISOString(),offers:[{provider:"Netflix",kind:"subscription"}]};
const kFilms = [42,43,44,44,46].map((id,index) => ({id:`task-${index}`,title:`Fictional ${id}`,status:"to-do",
  fields:{"POC TMDB ID":String(id),"POC Genre":"Drama"},live:{availability}}));
const kKeys = observedWatchlistKeys(source,kFilms,(item) => Number(item.fields["POC TMDB ID"]),(item) => item.id);
const kPrefs = {"task-0":{interest_score:8,watchlist:false,watched_at:null},"task-1":{interest_score:10,watchlist:false,watched_at:"2026-01-01T12:00:00Z"},"task-4":{interest_score:10,watchlist:true}};
const kOptions = {movaryWatchlistOnly:true,movaryWatchlistKeys:kKeys,preferences:kPrefs,provider:"Netflix",minimum:"8",genre:"Drama",sortInterest:true};
assert.deepEqual(filterFilms(kFilms,kOptions).map((item) => item.id),["task-1","task-0"]);
assert.deepEqual(filterFilms(kFilms,{...kOptions,watched:"marked",lifecycle:"to-do",freshnessFilter:"recent"}).map((item) => item.id),["task-1"]);
assert.deepEqual(filterFilms(kFilms,{...kOptions,movaryWatchlistKeys:null}),[],"unavailable source is not an empty or matching list");
assert.deepEqual(filterFilms(kFilms,{...kOptions,watchlistOnly:true}),[],"local and Movary selections are independent");
assert.equal(observedWatchlistKeys({status:"unknown"},kFilms,() => 42,() => "x"),null);

const yFilms = [42,43,44,44,46].map((id,index) => ({idReadable:`FILMPOC-${index}`,summary:`Fictional ${id}`,
  customFields:[{name:"FilmIQ TMDB ID",value:id},{name:"FilmIQ Genre",value:"Drama"},{name:"FilmIQ Lifecycle",value:{name:"Discovery"}}],live:{availability}}));
const yKeys = observedWatchlistKeys(source,yFilms,(item) => item.customFields[0].value,(item) => item.idReadable);
const yPrefs = {"FILMPOC-0":{interest_score:8,watchlist:false,watched_at:null},"FILMPOC-1":{interest_score:10,watchlist:false,watched_at:"2026-01-01T12:00:00Z"},"FILMPOC-4":{interest_score:10,watchlist:true}};
const yOptions = {movaryWatchlistOnly:true,movaryWatchlistKeys:yKeys,preferences:yPrefs,provider:"Netflix",minimum:"8",genre:"Drama",sortInterest:true};
assert.deepEqual(filterYoutrackFilms(yFilms,yOptions).map((item) => item.idReadable),["FILMPOC-1","FILMPOC-0"]);
assert.deepEqual(filterYoutrackFilms(yFilms,{...yOptions,localWatched:"watched",stateFilter:"Discovery",freshness:"recent"}).map((item) => item.idReadable),["FILMPOC-1"]);
assert.deepEqual(filterYoutrackFilms(yFilms,{...yOptions,movaryWatchlistKeys:null}),[]);
assert.deepEqual(filterYoutrackFilms(yFilms,{...yOptions,watchlistOnly:true}),[]);
const badge = (keys, filmKey) => renderToStaticMarkup(React.createElement(MovaryWatchlistBadge,{keys,filmKey}));
assert.match(badge(kKeys,"task-0"),/On observed Movary watchlist.*ID unverified/);
assert.match(badge(yKeys,"FILMPOC-1"),/On observed Movary watchlist.*ID unverified/);
assert.equal(badge(kKeys,"task-2"),"", "ambiguous IDs cannot get a badge");
assert.equal(badge(yKeys,"FILMPOC-4"),"", "absence does not claim a negative status");
assert.equal(badge(null,"FILMPOC-1"),"", "unavailable source does not get a badge");

const calls = [], props = {snapshot,films,getId,getKey,getTitle,onSelect:(film) => calls.push(["select",film.id]),onPrepare:(entry) => calls.push(["prepare",entry.tmdb_id]),prepareDisabled:false};
const rendered = renderToStaticMarkup(React.createElement(MovaryWatchlist,props));
for (const value of ["Movary watchlist", "2026-11-06T12:00:00Z", "Fictional existing", "Fictional missing", "2026-11-01 09:02:03", "Not in the loaded tracker records", "Preparing does not save or fetch metadata", "not independently verified"]) assert.ok(rendered.includes(value), `Missing ${value}`);
assert.doesNotMatch(rendered, /not on (?:the )?Movary watchlist/i);
assert.match(renderToStaticMarkup(React.createElement(MovaryWatchlist,{...props,snapshot:null})), /snapshot unavailable/i);
assert.match(renderToStaticMarkup(React.createElement(MovaryWatchlist,{...props,films:[...films,{id:"two",tmdb:42}]})), /Multiple tracker records/);
assert.match(renderToStaticMarkup(React.createElement(MovaryWatchlist,{...props,films:[{...films[0],title:"Different fictional title"}]})), /source title and tracker title differ/);
assert.doesNotMatch(rendered, /source title and tracker title differ/);

function elements(node) {
  if (!React.isValidElement(node)) return [];
  return [node,...React.Children.toArray(node.props.children).flatMap(elements)];
}
const buttons = elements(MovaryWatchlist(props)).filter((item) => item.type === "button");
assert.equal(buttons.length, 2);
buttons[0].props.onClick(); buttons[1].props.onClick();
assert.deepEqual(calls, [["select","one"],["prepare",43]]);
const disabled = elements(MovaryWatchlist({...props,prepareDisabled:true})).filter((item) => item.type === "button");
assert.equal(disabled[1].props.disabled, true);
console.log("Fictional Movary watchlist view keeps project scope, positive status and drafts separate");
