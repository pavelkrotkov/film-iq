import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import {transform} from "esbuild";
import React from "react";
import {renderToStaticMarkup} from "react-dom/server";
import {MOVARY_MAPPING_NOTICE, boundMovaryFilm, historicalMovaryHistories, movaryHistory, unboundMovaryHistory} from "./movary_history.js";
import {suppliedTmdbId} from "./youtrack_tmdb.js";

const source = await readFile(new URL("./youtrack.jsx", import.meta.url), "utf8");
const start = source.indexOf("{watchedHistory ? <section>");
const end = source.indexOf("\n        {!cacheFixture && <ReviewedCatalog", start);
assert.ok(start >= 0 && end > start);
const detail = source.slice(start, end);
const discovery = source.split("\n").find((line) => line.includes("visible.some((item) => boundMovaryFilm"));
assert.ok(discovery);
const {code} = await transform(`function Detail({watchedHistory,unboundHistory,historicalHistory=[]}) { return <>${detail}</>; }
function Discovery({visible,movary}) { return <>${discovery}</>; }
module.exports = {Detail,Discovery};`, {loader:"jsx",format:"cjs"});
const module = {exports:{}};
new Function("module","exports","React","MOVARY_MAPPING_NOTICE","boundMovaryFilm","suppliedTmdbId",code)(module,module.exports,React,MOVARY_MAPPING_NOTICE,boundMovaryFilm,suppliedTmdbId);
const entry = {tmdb_id:42,watched:true,played_watch_dates:[{date:null,plays:2},{date:"2001-02-03",plays:1},{date:"2001-02-03",plays:1}],history_export_dates:[null,"2001-02-03","2001-02-03"]};
const snapshot = {status:"available",films:{"FILMPOC-1":entry,"FILMPOC-2":{...entry,tmdb_id:null}}};
const item = (id,tmdb) => ({idReadable:id,customFields:[{name:"FilmIQ TMDB ID",value:tmdb}]});
const render = (component, props) => renderToStaticMarkup(React.createElement(component, props));
const history = movaryHistory(snapshot,"FILMPOC-1",42);
const details = render(module.exports.Detail,{watchedHistory:history});
assert.match(details,/matching source events/);
assert.match(details,/not been independently verified/);
assert.doesNotMatch(render(module.exports.Detail,{watchedHistory:null}),/matching source events/);
const unbound = render(module.exports.Detail,{watchedHistory:null,unboundHistory:unboundMovaryHistory(snapshot,"FILMPOC-2")});
assert.match(unbound,/Movary watched status unknown/);
assert.match(unbound,/Unverified Movary history for this issue/);
assert.match(unbound,/may not match the current film/);
assert.match(unbound,/does not mark the current film watched/);
assert.match(unbound,/Date unknown.*2 play\(s\)/);
assert.equal((unbound.match(/2001-02-03/g) || []).length,4,"repeated dates remain visible in both observations");
assert.doesNotMatch(unbound,/<h3>Watched in Movary<\/h3>/);
const v3 = {...snapshot,historical:[
  {issue_id:"FILMPOC-1",observed_at:"2026-01-01T12:00:00Z",reason:"unbound",film:{...entry,tmdb_id:null}},
  {issue_id:"FILMPOC-1",observed_at:"2026-02-01T12:00:00Z",reason:"superseded",film:entry},
]};
const historical = render(module.exports.Detail,{watchedHistory:null,historicalHistory:historicalMovaryHistories(v3,"FILMPOC-1")});
assert.match(historical,/Movary watched status unknown/);
assert.match(historical,/Unverified prior mapping/);
assert.match(historical,/Superseded prior observation/);
assert.match(historical,/2026-01-01T12:00:00Z/);
assert.match(historical,/2026-02-01T12:00:00Z/);
assert.match(historical,/do not determine the current film&#x27;s watched status/);
assert.equal((historical.match(/2001-02-03/g) || []).length,8,"each historical observation preserves both repeated sources");
assert.doesNotMatch(historical,/<h3>Watched in Movary<\/h3>/);
assert.match(render(module.exports.Detail,{watchedHistory:null,historicalHistory:null}),/Earlier Movary observations are unavailable/);
const shown = render(module.exports.Discovery,{visible:[item("FILMPOC-1",42),item("FILMPOC-2",43)],movary:snapshot});
assert.match(shown,/matching source events/);
assert.equal((shown.match(/not been independently verified/g) || []).length,1);
assert.equal(render(module.exports.Discovery,{visible:[item("FILMPOC-2",43)],movary:snapshot}).trim(),"");
assert.equal(render(module.exports.Discovery,{visible:[item("FILMPOC-1",43)],movary:snapshot}).trim(),"");
console.log("Fictional watched details and visible bound cards explain mapping uncertainty");
