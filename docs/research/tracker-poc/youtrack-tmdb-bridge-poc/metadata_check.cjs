const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const {execFileSync} = require('node:child_process');

let calls = 0;
const request = `import json,sys,urllib.request,urllib.error
url,token,body=sys.argv[1:]
req=urllib.request.Request(url+'/metadata',data=body.encode(),method='POST',headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'})
try:
 r=urllib.request.urlopen(req,timeout=5); code=r.status; data=r.read().decode()
except urllib.error.HTTPError as e:
 code=e.code; data=e.read().decode()
print(json.dumps({'code':code,'body':json.loads(data)}))`;

class FixtureConnection {
  constructor(url) { this.url = url; }
  bearerAuth(token) { this.token = token; }
  addHeader() {}
  postSync(route, _query, body) {
    assert.equal(route, '/metadata');
    calls++;
    const result = JSON.parse(execFileSync('python3', ['-c', request, this.url, this.token, body], {encoding: 'utf8'}));
    return {code: result.code, json: () => result.body};
  }
}

const code = fs.readFileSync(path.join(__dirname, 'metadata.js'), 'utf8');
const context = {exports: {}, require(name) {
  if (name.endsWith('/entities')) return {Field: {integerType: 'integer'}};
  if (name.endsWith('/http')) return {Connection: FixtureConnection};
  throw new Error('Unexpected module');
}};
vm.runInNewContext(code, context);
const endpoint = context.exports.httpHandler.endpoints[0];
assert.equal(endpoint.scope, 'issue');
assert.equal(context.exports.httpHandler.requirements.filmId.type, 'integer');

function invoke({id = 900000001, user = {login: 'fixture-user'}, project = 'FILMPOC', visible = true, bridgeToken = 'fixture-only-token', url = process.env.FIXTURE_BRIDGE_URL} = {}) {
  const result = {headers: {}};
  const ctx = {currentUser: user, settings: {bridgeToken, bridgeUrl: url},
    issue: {project: {key: project}, isReported: true, isVisibleTo: () => visible, fields: {'FilmIQ TMDB ID': id}},
    response: {addHeader(k, v) {result.headers[k] = v;}, json(v) {result.body = v;}, set code(v) {result.code = v;}}};
  endpoint.handle(ctx);
  assert.equal(result.headers['Cache-Control'], 'no-store');
  return result;
}

assert.equal(invoke({user: {login: 'guest'}}).code, 401);
assert.equal(invoke({visible: false}).code, 404);
assert.equal(invoke({project: 'FILMREAL'}).code, 404);
assert.equal(invoke({id: 11}).code, 403);
assert.equal(invoke({url: 'https://example.invalid'}).code, 503);
assert.equal(calls, 0);
assert.equal(invoke({bridgeToken: 'wrong'}).code, 502);
const success = invoke();
assert.equal(success.code, 200);
assert.equal(success.body.tmdb_id, 900000001);
assert.equal(success.body.title, 'Fictional film');
assert.equal(invoke({id: 900000002}).code, 429);
assert.equal(calls, 3);
console.log('Synthetic handler, authorization, loopback bridge and 429 checks passed');
