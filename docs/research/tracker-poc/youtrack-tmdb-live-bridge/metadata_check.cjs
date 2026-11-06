const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

let calls = 0, sent = null, responseCode = 200, responseId = 101, sentPath = '';
class Connection {
  constructor(url) { assert.equal(url, 'http://127.0.0.1:15178'); }
  bearerAuth(token) { assert.equal(token, 'synthetic-setting'); }
  addHeader() {}
  postSync(path, _query, body) {
    calls++; sentPath = path; sent = JSON.parse(body);
    return {code: responseCode, json: () => path === '/status' ?
      ({pace_enabled:true,refresh_enabled:false}) : path === '/catalog' ?
      ({status:'available',film:{tmdb_id:responseId,title:'Fictional'}}) :
      ({tmdb_id: responseId, title: 'Fictional', availability: {offers: []}})};
  }
}
const context = {exports: {}, require(name) {
  if (name.endsWith('/entities')) return {Field: {integerType: 'integer'}};
  if (name.endsWith('/http')) return {Connection};
  throw new Error('Unexpected module');
}};
vm.runInNewContext(fs.readFileSync(path.join(__dirname, 'metadata.js'), 'utf8'), context);
const endpoint = context.exports.httpHandler.endpoints[0];
const catalogEndpoint = context.exports.httpHandler.endpoints.find(item => item.path === '/catalog');
const cacheEndpoint = context.exports.httpHandler.endpoints.find(item => item.path === '/cached');
const statusEndpoint = context.exports.httpHandler.endpoints.find(item => item.path === '/status');
assert.equal(endpoint.scope, 'issue');
assert.equal(context.exports.httpHandler.requirements.filmId.type, 'integer');

function invoke({id = 101, login = 'fixture-user', project = 'FILMREAL', visible = true, banned = false, reported = true, catalog = false, cache = false, status = false} = {}) {
  const result = {headers: {}};
  (catalog ? catalogEndpoint : cache ? cacheEndpoint : status ? statusEndpoint : endpoint).handle({currentUser: {login, isBanned: banned}, settings: {bridgeToken: 'synthetic-setting'},
    issue: {summary:'Fictional', project: {key: project}, isReported: reported, isVisibleTo: () => visible, fields: {'FilmIQ TMDB ID': id}},
    request: {json: () => ({tmdb_id: 999})},
    response: {addHeader(k,v) {result.headers[k]=v;}, json(v) {result.body=v;}, set code(v) {result.code=v;}}});
  assert.equal(result.headers['Cache-Control'], 'no-store');
  return result;
}
assert.equal(invoke({login:'guest'}).code, 401);
assert.equal(invoke({banned:true}).code, 401);
assert.equal(invoke({project:'OTHER'}).code, 404);
assert.equal(invoke({visible:false}).code, 404);
assert.equal(invoke({reported:false}).code, 404);
assert.equal(invoke({id:0}).code, 400);
assert.equal(calls, 0);
assert.equal(invoke().code, 200);
assert.equal(sent.tmdb_id, 101); // Caller-supplied body never chooses the ID.
responseCode = 403; assert.equal(invoke().code, 403);
responseCode = 429; assert.equal(invoke().code, 429);
responseCode = 503; assert.equal(invoke().code, 503); assert.equal(invoke().body.error, 'Live refresh temporarily unavailable');
responseCode = 200; responseId = 999; assert.equal(invoke().code, 502);
responseId = 101; calls = 0;
assert.equal(catalogEndpoint.method, 'GET');
assert.equal(invoke({catalog:true,login:'guest'}).code, 401);
assert.equal(invoke({catalog:true,visible:false}).code, 404);
assert.equal(invoke({catalog:true,project:'OTHER'}).code, 404);
assert.equal(calls, 0);
assert.equal(invoke({catalog:true}).code, 200);
assert.equal(sentPath, '/catalog'); assert.equal(sent.tmdb_id, 101); assert.equal(sent.title, 'Fictional');
responseId = 999; assert.equal(invoke({catalog:true}).code, 503);
responseId = 101; calls = 0;
assert.equal(cacheEndpoint.method, 'GET');
assert.equal(invoke({cache:true,login:'guest'}).code, 401);
assert.equal(invoke({cache:true,visible:false}).code, 404);
assert.equal(invoke({cache:true,project:'OTHER'}).code, 404);
assert.equal(calls, 0);
assert.equal(invoke({cache:true}).code, 200);
assert.equal(sentPath, '/cache'); assert.equal(sent.tmdb_id, 101);
responseCode = 404; assert.equal(invoke({cache:true}).code, 404);
responseCode = 403; assert.equal(invoke({cache:true}).code, 403);
responseCode = 200; calls = 0;
assert.equal(statusEndpoint.method, 'GET');
assert.equal(invoke({status:true,login:'guest'}).code, 401);
assert.equal(invoke({status:true,visible:false}).code, 404);
assert.equal(invoke({status:true,project:'OTHER'}).code, 404);
assert.equal(calls, 0);
const runtime = invoke({status:true});
assert.equal(runtime.code, 200); assert.equal(runtime.body.pace_enabled,true); assert.equal(runtime.body.refresh_enabled,false);
assert.deepEqual(Object.keys(runtime.body).sort(),['pace_enabled','refresh_enabled']);
assert.equal(sentPath, '/status'); assert.equal(sent.tmdb_id, 101);
responseCode = 403; assert.equal(invoke({status:true}).code, 403);
console.log('Synthetic issue visibility, ID derivation, secret handoff and errors passed');
