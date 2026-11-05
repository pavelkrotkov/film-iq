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
    return {code: responseCode, json: () => path === '/catalog' ?
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
assert.equal(endpoint.scope, 'issue');
assert.equal(context.exports.httpHandler.requirements.filmId.type, 'integer');

function invoke({id = 101, login = 'fixture-user', project = 'FILMREAL', visible = true, banned = false, reported = true, catalog = false} = {}) {
  const result = {headers: {}};
  (catalog ? context.exports.httpHandler.endpoints[1] : endpoint).handle({currentUser: {login, isBanned: banned}, settings: {bridgeToken: 'synthetic-setting'},
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
responseCode = 503; assert.equal(invoke().code, 503);
responseCode = 200; responseId = 999; assert.equal(invoke().code, 502);
responseId = 101; calls = 0;
assert.equal(context.exports.httpHandler.endpoints[1].method, 'GET');
assert.equal(invoke({catalog:true,login:'guest'}).code, 401);
assert.equal(invoke({catalog:true,visible:false}).code, 404);
assert.equal(invoke({catalog:true,project:'OTHER'}).code, 404);
assert.equal(calls, 0);
assert.equal(invoke({catalog:true}).code, 200);
assert.equal(sentPath, '/catalog'); assert.equal(sent.tmdb_id, 101); assert.equal(sent.title, 'Fictional');
responseId = 999; assert.equal(invoke({catalog:true}).code, 503);
console.log('Synthetic issue visibility, ID derivation, secret handoff and errors passed');
