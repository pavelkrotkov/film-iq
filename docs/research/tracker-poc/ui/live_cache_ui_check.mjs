import assert from 'node:assert/strict';
import {availabilityTimeLabel, expireCachedResults, fetchCachedMovie, fetchTaskLiveMovie, hydrateCachedResult, mergeResult, refreshNotice} from './live_batch.js';
import {matchedLive} from './kaneo_identity.js';
import {attachMatchedLive, mergeLiveMetadata, mergeLiveResult, readLiveMetadata} from './youtrack_tmdb.js';
import {providerObservation, providerFreshness} from './youtrack_filters.js';

const expiry = new Date(Date.now() + 60000).toISOString();
const data = {tmdb_id:123, title:'Fictional', cache_expires_at:expiry, availability:{status:'unknown', offers:[]}};
const task = {id:'fictional-task', fields:{'POC TMDB ID':'123'}};
const actual = await fetchCachedMovie(task, null, async (url) => {
  assert.equal(url, 'http://localhost:15176/cache/fictional-task');
  return {ok:true,json:async () => data};
});
assert.equal(actual.tmdb_id,123);
await fetchTaskLiveMovie(task, null, async (url) => {
  assert.equal(url, 'http://localhost:15176/refresh/fictional-task');
  return {ok:true,json:async () => data};
});
await assert.rejects(fetchTaskLiveMovie(task, null, async () => ({ok:true,json:async () => ({...data, cache_expires_at:null})})));
await assert.rejects(fetchCachedMovie(task,null,async () => ({ok:true,json:async () => ({...data,cache_expires_at:'2000-01-01T00:00:00Z'})})));
const issue = {idReadable:'FILMPOC-1', customFields:[{name:'FilmIQ TMDB ID',value:123}]};
// Correcting an ID should replace only the old identity's cached entry, even
// when it previously failed. An in-flight read must not overwrite a newer result.
const older = {requestedId:122,data:{tmdb_id:122,title:'Fictional'}};
const taskWithTitle = {...task,title:'Fictional'};
const issueWithTitle = {...issue,summary:'Fictional'};
for (const entry of [older,{requestedId:122,error:'Fictional failure'}]) {
  const k = hydrateCachedResult({'fictional-task':entry},'fictional-task',123,data,entry);
  const y = hydrateCachedResult({'FILMPOC-1':entry},'FILMPOC-1',123,data,entry);
  assert.equal(matchedLive(taskWithTitle,k['fictional-task']),data);
  assert.equal(attachMatchedLive([issueWithTitle],y)[0].live,data);
}
const current = {'fictional-task':{requestedId:123,error:'Latest refresh failed'}};
const recovered = hydrateCachedResult(current,'fictional-task',123,data,current['fictional-task']);
assert.equal(recovered['fictional-task'].error,'Latest refresh failed','cache must not hide a refresh failure');
assert.equal(recovered['fictional-task'].data,data,'cache can supply data beneath the failure');
const currentSuccess = {'fictional-task':{requestedId:123,data:{...data,title:'Fresh explicit refresh'}}};
assert.equal(hydrateCachedResult(currentSuccess,'fictional-task',123,data,older),currentSuccess,'older pending read must not replace current live data');
assert.equal(hydrateCachedResult({},'fictional-task',123,{...data,tmdb_id:122})['fictional-task'],undefined);
const cached = await readLiveMetadata({fetchYouTrack:async (url, options) => {
  assert.equal(url,'issues/FILMPOC-1/extensionEndpoints/filmiq-tmdb-live-isolated/metadata/cached');
  assert.deepEqual(options,{method:'GET'});
  return data;
}},issue,{cacheOnly:true});
assert.equal(cached.cache_expires_at,expiry);
const attemptTime = new Date().toISOString();
const attempt = await readLiveMetadata({fetchYouTrack:async () => ({...data,availability:{status:'unknown',offers:[],checked_at:attemptTime}})},issue,{cacheOnly:true});
assert.equal(attempt.availability.checked_at,attemptTime);
assert.equal(providerFreshness(providerObservation({live:attempt})),'unknown');
assert.equal(availabilityTimeLabel('unknown',attemptTime),`Attempted: ${attemptTime}`);
assert.equal(availabilityTimeLabel('unknown',null),'Attempt time unknown');
assert.equal(availabilityTimeLabel('complete',attemptTime),`Checked: ${attemptTime}`);
const retained = await readLiveMetadata({fetchYouTrack:async () => ({
  ...data, synopsis:'Earlier synopsis', metadata_attempt:'incomplete', availability_attempt:'partial',
  availability:{status:'complete', offers:[{provider:'Fixture Stream',kind:'subscription'}]},
})},issue,{requireExpiry:true});
assert.equal(retained.synopsis,'Earlier synopsis');
assert.equal(retained.metadata_attempt,'incomplete');
assert.equal(retained.availability_attempt,'partial');
assert.equal(retained.availability.status,'complete');
assert.equal(refreshNotice({requestedId:123,data:retained},123,retained),'Your last in-app metadata and provider check was incomplete; shown data may come from another check.');
await assert.rejects(readLiveMetadata({fetchYouTrack:async () => ({...data, cache_expires_at:null})}, issue, {requireExpiry:true}));
await assert.rejects(readLiveMetadata({fetchYouTrack:async () => ({...data, cache_expires_at:'2000-01-01T00:00:00Z'})}, issue, {requireExpiry:true}));
const original = {cached:{data:cached},live:{data:{tmdb_id:123}}};
const after = expireCachedResults(original,Date.parse(expiry));
assert.equal(after.results.cached,undefined);
assert.deepEqual(after.results.live,original.live);

const oldExpiry = new Date(Date.now() + 30000).toISOString(), newExpiry = new Date(Date.now() + 120000).toISOString();
const previous = {...data,cache_expires_at:oldExpiry,poster_url:'fictional.jpg',availability:{status:'complete',offers:[{provider:'Fixture',kind:'subscription'}]}};
const newAvailability = {...data,cache_expires_at:newExpiry,poster_url:null,availability:{status:'complete',offers:[]}};
const newPoster = {...data,cache_expires_at:newExpiry,poster_url:'new-fictional.jpg',availability:{status:'unknown',offers:[]}};
for (const next of [newAvailability,newPoster]) {
  const kaneo = mergeResult({data:previous},{data:next}).data;
  const youtrack = mergeLiveMetadata(previous,next);
  assert.equal(kaneo.cache_expires_at,oldExpiry);
  assert.equal(youtrack.cache_expires_at,oldExpiry);
  if (!next.poster_url) { assert.equal(kaneo.poster_url,previous.poster_url); assert.equal(youtrack.poster_url,previous.poster_url); }
  else { assert.deepEqual(kaneo.availability,previous.availability); assert.deepEqual(youtrack.availability,previous.availability); }
}
const expired = {...previous,cache_expires_at:'2000-01-01T00:00:00Z'};
assert.equal(mergeResult({data:expired},{data:newAvailability}).data.poster_url,null);
assert.equal(mergeLiveMetadata(expired,newAvailability).poster_url,null);
assert.equal(mergeResult({data:expired},{data:newPoster}).data.availability.status,'unknown');
assert.equal(mergeLiveMetadata(expired,newPoster).availability.status,'unknown');
assert.equal(mergeResult({data:expired},{error:'failed'}).data,undefined);
assert.equal(mergeLiveResult({data:expired},{error:'failed'}).data,undefined);

// Expiring the earlier provider section permits a new cache-only read of the
// still-fresh metadata; the read never uses the refresh endpoint.
let cacheReads = 0;
const cleared = expireCachedResults({task:{data:previous}}, Date.parse(oldExpiry)).results;
assert.equal(cleared.task,undefined);
const refreshed = await fetchCachedMovie(task, null, async (url) => {
  cacheReads++;
  assert.equal(url, 'http://localhost:15176/cache/fictional-task');
  return {ok:true,json:async () => ({...data,cache_expires_at:newExpiry,synopsis:'Still fresh',availability:{status:'unknown',offers:[]}})};
});
assert.equal(refreshed.synopsis,'Still fresh');
assert.equal(refreshed.availability.status,'unknown');
assert.equal(cacheReads,1);
console.log('Cache-only routes and display expiry passed');
