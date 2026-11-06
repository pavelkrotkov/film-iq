import assert from "node:assert/strict";
import {historicalMovaryHistories, movaryHistory, unboundMovaryHistory} from "./movary_history.js";

const record = {tmdb_id:42,watched:true, played_watch_dates:[{date:null,plays:2},{date:"2001-02-03",plays:3},{date:"2001-02-03",plays:1}], history_export_dates:[null,"2001-02-03","2001-02-03"]};
const snapshot = {status:"available",observed_at:"2026-11-05T12:00:00Z",films:{"FILMPOC-1":record}};
const history = movaryHistory(snapshot, "FILMPOC-1", 42);
assert.equal(history.observedAt, snapshot.observed_at);
assert.deepEqual(history.plays, record.played_watch_dates, "play counts, duplicates and unknown dates remain separate");
assert.deepEqual(history.exportDates, record.history_export_dates, "export dates must not be deduplicated or added to plays");
assert.equal(movaryHistory(snapshot, "FILMPOC-2", 42), null, "a missing film is unknown");
assert.equal(movaryHistory({...snapshot,status:"unknown"}, "FILMPOC-1", 42), null);
assert.equal(movaryHistory(snapshot, "FILMPOC-1", 43), null, "a corrected ID cannot inherit old watched history");
assert.equal(movaryHistory({...snapshot,films:{"FILMPOC-1":{...record,tmdb_id:null}}}, "FILMPOC-1", 42), null, "an explicitly unbound identity remains unknown");
assert.equal(movaryHistory({...snapshot,films:{"FILMPOC-1":{...record,tmdb_id:undefined}}}, "FILMPOC-1", 42), null, "legacy mappings have unknown identity");
const unbound = {...snapshot,films:{"FILMPOC-1":{...record,tmdb_id:null}}};
assert.deepEqual(unboundMovaryHistory(unbound,"FILMPOC-1"),history, "unbound evidence preserves both histories exactly");
assert.equal(unboundMovaryHistory(snapshot,"FILMPOC-1"),null, "a bound entry does not become unbound evidence after an ID edit");
assert.equal(unboundMovaryHistory({...snapshot,films:{"FILMPOC-1":{...record,tmdb_id:undefined}}},"FILMPOC-1"),null, "legacy mappings remain unknown");
assert.equal(unboundMovaryHistory({...unbound,status:"unknown"},"FILMPOC-1"),null);
assert.deepEqual(historicalMovaryHistories(snapshot,"FILMPOC-1"),[], "older snapshots do not invent historical entries");
const v3 = {...snapshot,historical:[
  {issue_id:"FILMPOC-1",observed_at:"2026-01-01T12:00:00Z",reason:"unbound",film:{...record,tmdb_id:null}},
  {issue_id:"FILMPOC-1",observed_at:"2026-02-01T12:00:00Z",reason:"superseded",film:record},
  {issue_id:"FILMPOC-2",observed_at:"2026-02-01T12:00:00Z",reason:"unbound",film:{...record,tmdb_id:null}},
]};
const previous = historicalMovaryHistories(v3,"FILMPOC-1");
assert.deepEqual(previous.map((item) => item.reason),["unbound","superseded"]);
assert.deepEqual(previous.map((item) => item.observedAt),["2026-01-01T12:00:00Z","2026-02-01T12:00:00Z"]);
assert.deepEqual(previous[0].plays,record.played_watch_dates);
assert.deepEqual(previous[0].exportDates,record.history_export_dates);
assert.deepEqual(historicalMovaryHistories(v3,"FILMPOC-3"),[]);
assert.equal(historicalMovaryHistories({...v3,historical:null},"FILMPOC-1"),null);
assert.equal(historicalMovaryHistories({...v3,historical:[{...v3.historical[0],observed_at:"2026-02-30T00:00:00Z"}]},"FILMPOC-1"),null);
assert.equal(historicalMovaryHistories({...v3,historical:[{...v3.historical[0],reason:"superseded"}]},"FILMPOC-1"),null);
assert.equal(historicalMovaryHistories({...v3,historical:[{...v3.historical[0],film:{...record,tmdb_id:null,played_watch_dates:"invalid"}}]},"FILMPOC-1")[0].plays,null);
assert.equal(movaryHistory({...snapshot,films:{"FILMPOC-1":{...record,played_watch_dates:[{date:"2001-02-30",plays:1}]}}}, "FILMPOC-1", 42).plays, null);
assert.equal(movaryHistory({...snapshot,films:{"FILMPOC-1":{...record,history_export_dates:["invalid"]}}}, "FILMPOC-1", 42).exportDates, null);
console.log("Movary history preserves separate plays, unknown dates and repeated exports");
