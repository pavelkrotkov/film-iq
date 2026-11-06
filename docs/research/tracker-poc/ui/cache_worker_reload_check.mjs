import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {transform} from 'esbuild';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {fetchCachedMovie, hydrateCachedResult, tmdbId} from './live_batch.js';
import {readLiveMetadata, suppliedTmdbId} from './youtrack_tmdb.js';

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
    'host','suppliedTmdbId', effect)(useEffect,true,false,[film],0,
      (item, signal) => fetchCachedMovie(item, signal, fakeFetch),tmdbId,setLiveResults,
      hydrateCachedResult,liveResultsRef,readLiveMetadata,host,suppliedTmdbId);
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
console.log('Both cache-only effects show worker updates and preserve newer explicit refreshes');
