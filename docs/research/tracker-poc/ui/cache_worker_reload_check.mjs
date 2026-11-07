import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {transform} from 'esbuild';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {fetchCachedMovie, hydrateCachedResult, tmdbId} from './live_batch.js';
import {readLiveMetadata, suppliedTmdbId} from './youtrack_tmdb.js';
import {boundedRead} from './youtrack_loading.js';

const expiry = new Date(Date.now() + 60000).toISOString();
const cacheData = {tmdb_id:123, title:'Fictional film', synopsis:'Updated by fictional worker',
  cache_expires_at:expiry, availability:{status:'unknown', offers:[], checked_at:null}};
const previous = {requestedId:123, data:{...cacheData, synopsis:'Earlier synopsis'}};

// Run the actual cache-only effects with controlled responses. No provider or
// tracker calls are made; the fake host/fetcher return fictional cache data.
async function exercise(kind, race = null, initial = previous) {
  const filename = kind === 'kaneo' ? 'src.jsx' : 'youtrack.jsx';
  const source = readFileSync(new URL(filename, import.meta.url), 'utf8');
  const marker = kind === 'kaneo'
    ? '  useEffect(() => {\n    if (!liveCache || cacheFixture) return;'
    : '  useEffect(() => {\n    if (!liveCache) return;';
  const start = source.indexOf(marker), endMarker = '  }, [films, cacheGeneration]);';
  const end = source.indexOf(endMarker, start);
  assert.ok(start >= 0 && end >= 0, `${kind} cache effect not found`);
  const effect = source.slice(start, end + endMarker.length);
  const key = kind === 'kaneo' ? 'fictional-task' : 'FILMPOC-1';
  const film = kind === 'kaneo'
    ? {id:key, title:'Fictional film', fields:{'POC TMDB ID':'123'}}
    : {idReadable:key, summary:'Fictional film', customFields:[{name:'FilmIQ TMDB ID',value:123}]};
  let state = {[key]: initial}, cleanup, requests = 0, resolve;
  const pending = new Promise((done) => {resolve = done;});
  const liveResultsRef = {current:state};
  const setLiveResults = (update) => {state = update(state); liveResultsRef.current = state;};
  const useEffect = (callback) => {cleanup = callback();};
  const fakeFetch = async (url) => {
    assert.equal(url, 'http://localhost:15176/cache/fictional-task'); requests++;
    return {ok:true,json:async () => pending};
  };
  const host = {fetchYouTrack:async (url, options) => {
    assert.equal(url, 'issues/FILMPOC-1/extensionEndpoints/filmiq-tmdb-live-isolated/metadata/cached');
    assert.deepEqual(options, {method:'GET'}); requests++; return pending;
  }};
  new Function('useEffect','liveCache','cacheFixture','films','cacheGeneration','fetchCachedMovie',
    'tmdbId','setLiveResults','hydrateCachedResult','liveResultsRef','readLiveMetadata',
    'host','suppliedTmdbId','boundedRead','pendingCacheReads','setCacheNotice', effect)(useEffect,true,false,[film],0,
      (item, signal) => fetchCachedMovie(item, signal, fakeFetch),tmdbId,setLiveResults,
      hydrateCachedResult,liveResultsRef,readLiveMetadata,host,suppliedTmdbId,boundedRead,{current:0},() => {});
  if (race) {
    state = {[key]: race};
    liveResultsRef.current = state;
  }
  resolve(cacheData);
  await new Promise((done) => setImmediate(done));
  cleanup?.();
  assert.equal(requests, 1);
  return state[key];
}

for (const kind of ['kaneo', 'youtrack']) {
  const updated = await exercise(kind);
  assert.equal(updated.data.synopsis, cacheData.synopsis, `${kind}: reload should show worker update`);
  const explicit = {requestedId:123,data:{...cacheData,synopsis:'Newer explicit refresh'}};
  assert.equal(await exercise(kind, explicit), explicit, `${kind}: older cache read must not replace explicit refresh`);
  const failure = {requestedId:123,data:previous.data,error:'Latest explicit refresh failed'};
  assert.equal(await exercise(kind, failure), failure, `${kind}: older cache read must not hide explicit failure`);
  const afterFailure = await exercise(kind, null, failure);
  assert.equal(afterFailure.error,failure.error,`${kind}: reload must preserve a prior failure notice`);
  assert.equal(afterFailure.data.synopsis,cacheData.synopsis,`${kind}: reload can still show a worker update`);
  const partial = {requestedId:123,data:{...previous.data,metadata_attempt:'incomplete',availability_attempt:'partial'}};
  const afterPartial = await exercise(kind, null, partial);
  assert.equal(afterPartial.data.metadata_attempt,'incomplete',`${kind}: reload must preserve metadata-attempt notice`);
  assert.equal(afterPartial.data.availability_attempt,'partial',`${kind}: reload must preserve provider-attempt notice`);
  assert.equal(afterPartial.data.synopsis,cacheData.synopsis,`${kind}: incomplete-attempt notice must not hide worker data`);

  // Render the actual detail notices after a worker update. The saved flags
  // describe the last in-app attempt, not the order of external worker reads.
  const source = readFileSync(new URL(kind === 'kaneo' ? 'src.jsx' : 'youtrack.jsx', import.meta.url),'utf8');
  const variable = kind === 'kaneo' ? 'liveMovie' : 'live';
  const lines = ['metadata_attempt','availability_attempt'].map((name) =>
    source.split('\n').find((line) => line.includes(`${variable}.${name} && <p>`)));
  assert.ok(lines.every(Boolean), `${kind}: detail notices not found`);
  const {code} = await transform(`function Notice({data}) { const ${variable}=data; return <>${lines.map((line) => line.trim()).join('')}</>; } module.exports=Notice;`,{loader:'jsx',format:'cjs'});
  const module = {exports:{}};
  new Function('module','exports','React',code)(module,module.exports,React);
  const rendered = renderToStaticMarkup(React.createElement(module.exports,{data:afterPartial.data}));
  assert.match(rendered,/last in-app metadata check was incomplete/);
  assert.match(rendered,/last in-app provider check was partial/);
  assert.match(rendered,/may come from another check/);
  assert.doesNotMatch(rendered,/Latest|earlier provider observation/);
}

// A stalled first cache read must not indefinitely hide later films' artwork.
async function stalledFirstCacheRead(kind, navigate = false) {
  const source = readFileSync(new URL(kind === 'kaneo' ? 'src.jsx' : 'youtrack.jsx', import.meta.url), 'utf8');
  const markerStart = kind === 'kaneo'
    ? '  useEffect(() => {\n    if (!liveCache || cacheFixture) return;'
    : '  useEffect(() => {\n    if (!liveCache) return;';
  const start = source.indexOf(markerStart);
  const marker = '  }, [films, cacheGeneration]);';
  const end = source.indexOf(marker, start);
  assert.ok(start >= 0 && end >= 0);
  const effect = source.slice(start, end + marker.length);
  const films = [1, 2].map((number) => kind === 'kaneo'
    ? {id:`fictional-task-${number}`, title:'Fictional film', fields:{'POC TMDB ID':'123'}}
    : {idReadable:`FILMPOC-${number}`, summary:'Fictional film', customFields:[{name:'FilmIQ TMDB ID',value:123}]});
  let cleanup, state = {}, reads = [], signals = [];
  let resolveFirst;
  const first = new Promise((resolve) => {resolveFirst = resolve;});
  const liveResultsRef = {current:state};
  const host = {fetchYouTrack:(url) => {
    reads.push(url);
    return url.includes('FILMPOC-1/') ? first : Promise.resolve(cacheData);
  }};
  const fakeFetch = async (url, options) => {
    reads.push(url);
    signals.push(options.signal);
    return {ok:true, json:() => url.endsWith('-1') ? first : Promise.resolve(cacheData)};
  };
  new Function('useEffect','liveCache','cacheFixture','films','cacheGeneration','liveResultsRef','setLiveResults',
    'readLiveMetadata','host','suppliedTmdbId','fetchCachedMovie','tmdbId','hydrateCachedResult','boundedRead',
    'pendingCacheReads','setCacheNotice', effect)(
      (callback) => {cleanup = callback();},true,false,films,0,liveResultsRef,
      (update) => {state = update(state); liveResultsRef.current = state;},readLiveMetadata,host,suppliedTmdbId,
      (item, signal) => fetchCachedMovie(item, signal, fakeFetch),tmdbId,hydrateCachedResult,
      (operation) => boundedRead(operation, 15),{current:0},() => {});
  if (navigate) {
    await Promise.resolve(); // The first request has started before navigation.
    cleanup?.();
    resolveFirst({...cacheData, title:'Result after navigation'});
  }
  await new Promise((resolve) => setTimeout(resolve, 40));
  if (navigate) {
    assert.equal(reads.length, 1, `${kind}: navigation must stop further reads`);
    assert.deepEqual(state, {}, `${kind}: navigation must suppress pending results`);
  } else {
    assert.equal(reads.length, 2, `${kind}: later film must be read after the first times out`);
    const second = kind === 'kaneo' ? 'fictional-task-2' : 'FILMPOC-2';
    assert.equal(state[second]?.data?.title, 'Fictional film');
  }
  resolveFirst({...cacheData, title:'Late stale response'});
  await new Promise((resolve) => setImmediate(resolve));
  const firstKey = kind === 'kaneo' ? 'fictional-task-1' : 'FILMPOC-1';
  assert.equal(state[firstKey], undefined, `${kind}: late or navigated response stays unknown`);
  if (kind === 'kaneo') assert.equal(signals[0].aborted, true, 'timed-out or navigated fetch must be aborted');
  cleanup?.();
}
for (const kind of ['kaneo', 'youtrack']) {
  await stalledFirstCacheRead(kind);
  await stalledFirstCacheRead(kind, true);
}

// YouTrack's Host API has no exposed abort signal. Bound unresolved reads
// across refreshes and explain why the remaining cache data is unavailable.
async function hostStallsAreBounded() {
  const source = readFileSync(new URL('youtrack.jsx', import.meta.url), 'utf8');
  const start = source.indexOf('  useEffect(() => {\n    if (!liveCache) return;');
  const marker = '  }, [films, cacheGeneration]);';
  const end = source.indexOf(marker, start);
  assert.ok(start >= 0 && end >= 0);
  const effect = source.slice(start, end + marker.length);
  const films = [1, 2, 3].map((number) => ({idReadable:`FILMPOC-${number}`, summary:'Fictional film',
    customFields:[{name:'FilmIQ TMDB ID',value:123}]}));
  const pendingCacheReads = {current:0}, liveResultsRef = {current:{}};
  let calls = 0, notice = '', cleanup;
  const host = {fetchYouTrack:() => {calls++; return new Promise(() => {});}};
  const run = () => new Function('useEffect','liveCache','films','cacheGeneration','liveResultsRef',
    'setLiveResults','readLiveMetadata','host','suppliedTmdbId','hydrateCachedResult','boundedRead',
    'pendingCacheReads','setCacheNotice', effect)(
      (callback) => {cleanup = callback();},true,films,0,liveResultsRef,() => {},readLiveMetadata,host,
      suppliedTmdbId,hydrateCachedResult,(operation) => boundedRead(operation, 15),
      pendingCacheReads,(value) => {notice = value;});
  run();
  await new Promise((resolve) => setTimeout(resolve, 50));
  assert.equal(calls, 2);
  assert.equal(pendingCacheReads.current, 2);
  assert.match(notice, /paused.*reload this page/i);
  cleanup();
  run();
  await new Promise((resolve) => setTimeout(resolve, 5));
  assert.equal(calls, 2, 'refresh must not accumulate uncancellable Host requests');
  cleanup();
}
await hostStallsAreBounded();
console.log('Both cache-only effects show worker updates and preserve newer explicit refreshes');
