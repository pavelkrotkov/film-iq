import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {ACCESS_DENIED_MESSAGE, AccessDeniedError, accessDenied, fetchCachedMovie, fetchLiveMovie, fetchTaskLiveMovie, runBatch, runRemainingBatch, tmdbId} from "./live_batch.js";
import {LiveRateLimited, mergeLiveResult, readLiveMetadata, runLiveBatch, runRemainingLive, suppliedTmdbId} from "./youtrack_tmdb.js";

const tasks = [1,2,3].map((id) => ({id:`fictional-${id}`,fields:{"POC TMDB ID":String(id)}}));
const issues = [1,2,3].map((id) => ({idReadable:`FILMPOC-${id}`,customFields:[{name:"FilmIQ TMDB ID",value:id}]}));
for (const status of [401,403]) {
  let calls = 0;
  const responses = [];
  const result = await runBatch(tasks, (id,signal) => fetchTaskLiveMovie(tasks[id-1], signal, async () => {
    calls++;
    return id === 2 ? {status,ok:false} : {status:200,ok:true,json:async () => ({tmdb_id:id,cache_expires_at:new Date(Date.now()+60000).toISOString(),availability:{offers:[]}})};
  }), new AbortController().signal, (_,value) => responses.push(value));
  assert.equal(calls,2,"denial stops before the next film");
  assert.equal(result.accessDenied,true);
  assert.equal(responses[1].error,ACCESS_DENIED_MESSAGE);
  assert.equal(result.rateLimited,false);
  await assert.rejects(fetchLiveMovie(1,null,async () => ({status,ok:false})),AccessDeniedError);
  await assert.rejects(fetchCachedMovie(tasks[0],null,async () => ({status,ok:false})),AccessDeniedError);
  calls=0;
  const remaining = await runRemainingBatch(tasks, async () => {calls++;throw new AccessDeniedError();},new AbortController().signal,()=>{});
  assert.equal(calls,1); assert.equal(remaining.accessDenied,true);

  const failure = Object.assign(new Error("fictional denied response"),{response:{status}});
  await assert.rejects(readLiveMetadata({fetchYouTrack:async () => {throw failure;}},issues[0]),AccessDeniedError);
  await assert.rejects(readLiveMetadata({fetchYouTrack:async () => ({status})},issues[0]),AccessDeniedError);
  let ytCalls=0; const ytResults=[];
  const host={fetchYouTrack:async () => {ytCalls++;throw failure;}};
  const yt = await runLiveBatch(host,issues,()=>true,(_,value)=>ytResults.push(value));
  assert.equal(ytCalls,1); assert.equal(yt.accessDenied,true); assert.equal(ytResults[0].error,ACCESS_DENIED_MESSAGE);
  ytCalls=0;
  const all = await runRemainingLive(host,issues,()=>true,()=>{});
  assert.equal(ytCalls,1); assert.equal(all.accessDenied,true);
}
assert.equal(accessDenied(new Error("Fictional film 403 unavailable")),false,"an unrelated number must not be treated as an HTTP status");
assert.equal(accessDenied(new Error("HTTP 403 Forbidden")),true);
assert.equal(accessDenied({status:500}),false);

const kaneoSource = readFileSync(new URL("./src.jsx",import.meta.url),"utf8");
const fixtureStart=kaneoSource.indexOf("async function fixtureMovie(");
const fixtureEnd=kaneoSource.indexOf("function ProviderBadges(",fixtureStart);
assert.ok(fixtureStart>=0 && fixtureEnd>fixtureStart);
let fixtureCalls=0;
const fixtureMovie=new Function("fixtureIds","tmdbId","fetch","accessDenied","AccessDeniedError",`${kaneoSource.slice(fixtureStart,fixtureEnd)};return fixtureMovie;`)(new Set([900000001,900000002]),tmdbId,async()=>{fixtureCalls++;return {ok:false,status:403};},accessDenied,AccessDeniedError);
const fixtureTasks=[900000001,900000002].map((id)=>({id:`fixture-${id}`,fields:{"POC TMDB ID":String(id)}}));
const fixtureResult=await runBatch(fixtureTasks,(id,signal)=>fixtureMovie(fixtureTasks.find((item)=>tmdbId(item)===id),signal),new AbortController().signal,()=>{});
assert.equal(fixtureCalls,1); assert.equal(fixtureResult.accessDenied,true);

// Exercise the actual YouTrack single-film handler with a previous good result.
const source = readFileSync(new URL("./youtrack.jsx",import.meta.url),"utf8");
const start=source.indexOf("  async function loadLiveMetadata() {");
const end=source.indexOf("  async function loadNextLiveBatch(",start);
assert.ok(start>=0 && end>start);
const make=new Function("film","suppliedTmdbId","liveRequest","liveRateLimited","project","setLiveBusy","readLiveMetadata","host","projectRef","setLiveResults","mergeLiveResult","LiveRateLimited","setLiveRateLimited","AccessDeniedError","ACCESS_DENIED_MESSAGE",`${source.slice(start,end)};return loadLiveMetadata;`);
const previous={tmdb_id:1,title:"Fictional",availability:{status:"complete",offers:[]}};
let state={"FILMPOC-1":{requestedId:1,data:previous}}, busy=false, limited=false;
const action=make(issues[0],suppliedTmdbId,{current:false},false,"FILMPOC",(value)=>busy=value,readLiveMetadata,{fetchYouTrack:async()=>{throw Object.assign(new Error("denied"),{status:403});}},{current:"FILMPOC"},(change)=>state=change(state),mergeLiveResult,LiveRateLimited,(value)=>limited=value,AccessDeniedError,ACCESS_DENIED_MESSAGE);
await action();
assert.equal(state["FILMPOC-1"].error,ACCESS_DENIED_MESSAGE);
assert.equal(state["FILMPOC-1"].data,previous,"a denied refresh retains prior valid data");
assert.equal(busy,false); assert.equal(limited,false);
console.log("Fictional 401/403 stop batches and display denial without changing stored films");
