import assert from "node:assert/strict";
import {movaryHistory} from "./movary_history.js";

const record = {watched:true, played_watch_dates:[{date:null,plays:2},{date:"2001-02-03",plays:3},{date:"2001-02-03",plays:1}], history_export_dates:[null,"2001-02-03","2001-02-03"]};
const snapshot = {status:"available",observed_at:"2026-11-05T12:00:00Z",films:{"FILMPOC-1":record}};
const history = movaryHistory(snapshot, "FILMPOC-1");
assert.equal(history.observedAt, snapshot.observed_at);
assert.deepEqual(history.plays, record.played_watch_dates, "play counts, duplicates and unknown dates remain separate");
assert.deepEqual(history.exportDates, record.history_export_dates, "export dates must not be deduplicated or added to plays");
assert.equal(movaryHistory(snapshot, "FILMPOC-2"), null, "a missing film is unknown");
assert.equal(movaryHistory({...snapshot,status:"unknown"}, "FILMPOC-1"), null);
assert.equal(movaryHistory({...snapshot,films:{"FILMPOC-1":{...record,played_watch_dates:[{date:"2001-02-30",plays:1}]}}}, "FILMPOC-1").plays, null);
assert.equal(movaryHistory({...snapshot,films:{"FILMPOC-1":{...record,history_export_dates:["invalid"]}}}, "FILMPOC-1").exportDates, null);
console.log("Movary history preserves separate plays, unknown dates and repeated exports");
