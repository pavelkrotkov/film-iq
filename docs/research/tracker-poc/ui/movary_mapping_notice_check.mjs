import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import {transform} from "esbuild";
import React from "react";
import {renderToStaticMarkup} from "react-dom/server";
import {MOVARY_MAPPING_NOTICE, boundMovaryFilm, movaryHistory} from "./movary_history.js";
import {suppliedTmdbId} from "./youtrack_tmdb.js";

const source = await readFile(new URL("./youtrack.jsx", import.meta.url), "utf8");
const start = source.indexOf("{watchedHistory ? <section>");
const end = source.indexOf("\n        {!cacheFixture && <ReviewedCatalog", start);
assert.ok(start >= 0 && end > start);
const detail = source.slice(start, end);
const discovery = source.split("\n").find((line) => line.includes("visible.some((item) => boundMovaryFilm"));
assert.ok(discovery);
const {code} = await transform(`function Detail({watchedHistory}) { return <>${detail}</>; }
function Discovery({visible,movary}) { return <>${discovery}</>; }
module.exports = {Detail,Discovery};`, {loader:"jsx",format:"cjs"});
const module = {exports:{}};
new Function("module","exports","React","MOVARY_MAPPING_NOTICE","boundMovaryFilm","suppliedTmdbId",code)(module,module.exports,React,MOVARY_MAPPING_NOTICE,boundMovaryFilm,suppliedTmdbId);
const entry = {tmdb_id:42,watched:true,played_watch_dates:[],history_export_dates:[]};
const snapshot = {status:"available",films:{"FILMPOC-1":entry,"FILMPOC-2":{...entry,tmdb_id:null}}};
const item = (id,tmdb) => ({idReadable:id,customFields:[{name:"FilmIQ TMDB ID",value:tmdb}]});
const render = (component, props) => renderToStaticMarkup(React.createElement(component, props));
const history = movaryHistory(snapshot,"FILMPOC-1",42);
const details = render(module.exports.Detail,{watchedHistory:history});
assert.match(details,/matching source events/);
assert.match(details,/not been independently verified/);
assert.doesNotMatch(render(module.exports.Detail,{watchedHistory:null}),/matching source events/);
const shown = render(module.exports.Discovery,{visible:[item("FILMPOC-1",42),item("FILMPOC-2",43)],movary:snapshot});
assert.match(shown,/matching source events/);
assert.equal((shown.match(/not been independently verified/g) || []).length,1);
assert.equal(render(module.exports.Discovery,{visible:[item("FILMPOC-2",43)],movary:snapshot}).trim(),"");
assert.equal(render(module.exports.Discovery,{visible:[item("FILMPOC-1",43)],movary:snapshot}).trim(),"");
console.log("Fictional watched details and visible bound cards explain mapping uncertainty");
