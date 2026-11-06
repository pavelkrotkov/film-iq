import assert from "node:assert/strict";
import {createRequire} from "node:module";
import {build} from "esbuild";
import React from "react";
import {renderToStaticMarkup} from "react-dom/server";

const require = createRequire(import.meta.url);
const built = await build({entryPoints:[new URL("./movary_watchlist.jsx", import.meta.url).pathname], bundle:true, format:"cjs", platform:"node", external:["react"], write:false});
const module = {exports:{}};
new Function("require", "module", "exports", built.outputFiles[0].text)(require, module, module.exports);
const {MovaryWatchlist, reconcileMovaryWatchlist, watchlistForProject} = module.exports;
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
