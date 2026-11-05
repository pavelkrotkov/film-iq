/* Synthetic handler check; no calls to YouTrack, Movary or real user data. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

let visible = true;
const registry = {
  'FILMPOC-1': {project: {key: 'FILMPOC'}, isReported: true, isVisibleTo: () => visible},
  'FILMREAL-1': {project: {key: 'FILMREAL'}, isReported: true, isVisibleTo: () => true},
  'OTHER-1': {project: {key: 'OTHER'}, isReported: true, isVisibleTo: () => true},
};
const context = {
  exports: {},
  require(name) {
    assert.equal(name, '@jetbrains/youtrack-scripting-api/entities');
    return {Issue: {findById(id) { return registry[id] || null; }}};
  },
};
vm.runInNewContext(fs.readFileSync(path.join(__dirname, '../movary.js'), 'utf8'), context);
const endpoints = context.exports.httpHandler.endpoints;
const users = Object.fromEntries(['alice', 'bob', 'legacy', 'empty', 'guest'].map(login => [login, {
  login, isBanned: false, extensionProperties: {filmPreferences: 'unchanged'},
}]));

function call(user, method, endpoint, input) {
  const ctx = {
    currentUser: users[user], request: {json: () => input, getParameter: key => input?.[key] ?? null},
    response: {code: 200, json(value) { this.value = value; }},
  };
  endpoints.find(item => item.method === method && item.path === endpoint).handle(ctx);
  return JSON.parse(JSON.stringify({status: ctx.response.code, value: ctx.response.value}));
}

const watched = {watched: true, played_watch_dates: [{date: null, plays: 2}, {date: '2026-01-05', plays: 3}],
  history_export_dates: [null, '2026-01-05', '2026-01-05']};
const poc = {version: 'youtrack-poc-movary-watched-v1', source: 'Movary', complete: true,
  observed_at: '2026-11-05T12:00:00+00:00', project: 'FILMPOC', films: {'FILMPOC-1': watched}};
const real = {...poc, project: 'FILMREAL', observed_at: '2026-11-04T12:00:00+00:00', films: {'FILMREAL-1': watched}};
assert.equal(call('alice', 'GET', '/watched', {}).status, 400);
assert.deepEqual(call('alice', 'GET', '/watched', {project: 'FILMPOC'}).value,
  {status: 'unknown', source: 'Movary', observed_at: null, films: {}});
assert.equal(call('guest', 'GET', '/watched', {project: 'FILMPOC'}).status, 401);
assert.equal(call('alice', 'POST', '/import', poc).status, 200);
assert.deepEqual(call('alice', 'GET', '/watched', {project: 'FILMPOC'}).value.films, poc.films);
assert.equal(call('alice', 'GET', '/watched', {project: 'FILMREAL'}).value.status, 'unknown');
assert.deepEqual(call('bob', 'GET', '/watched', {project: 'FILMPOC'}).value.films, {});
assert.equal(users.alice.extensionProperties.filmPreferences, 'unchanged');
const first = users.alice.extensionProperties.filmMovarySnapshot;
assert.equal(call('alice', 'POST', '/import', {...poc, observed_at: '2026-11-04T12:00:00+00:00'}).status, 409);
assert.equal(users.alice.extensionProperties.filmMovarySnapshot, first);
assert.equal(call('alice', 'POST', '/import', poc).status, 200);
assert.equal(users.alice.extensionProperties.filmMovarySnapshot, first);
// An independently older source timestamp may populate the other project.
assert.equal(call('alice', 'POST', '/import', real).status, 200);
assert.deepEqual(call('alice', 'GET', '/watched', {project: 'FILMPOC'}).value.films, poc.films);
assert.deepEqual(call('alice', 'GET', '/watched', {project: 'FILMREAL'}).value.films, real.films);
const newer = {...poc, observed_at: '2026-11-05T12:00:00.000002Z'};
assert.equal(call('alice', 'POST', '/import', newer).status, 200);
const old = users.alice.extensionProperties.filmMovarySnapshot;
assert.equal(call('alice', 'POST', '/import', {...poc, observed_at: '2026-11-05T12:00:00.000001Z'}).status, 409);
assert.equal(call('alice', 'POST', '/import', {...poc, observed_at: '2026-11-05T07:00:00.000001-05:00'}).status, 409);
assert.equal(call('alice', 'POST', '/import', {...real, observed_at: '2026-11-03T12:00:00Z'}).status, 409);
assert.equal(users.alice.extensionProperties.filmMovarySnapshot, old);
assert.equal(call('alice', 'POST', '/import', {...poc, films: {...poc.films, 'OTHER-1': watched}}).status, 400);
assert.equal(call('alice', 'POST', '/import', {...poc, films: {'FILMREAL-1': watched}}).status, 400);
assert.equal(call('alice', 'POST', '/import', {...poc, films: {...poc.films, 'FILMPOC-404': watched}}).status, 404);
assert.equal(call('alice', 'POST', '/import', {...poc, project: 'OTHER', films: {}}).status, 400);
assert.equal(call('alice', 'POST', '/import', {...poc, films: {'FILMPOC-1': {...watched, personal_notes: 'bad'}}}).status, 400);
assert.equal(call('alice', 'POST', '/import', {...poc, films: {'FILMPOC-1': {...watched, played_watch_dates: [{date: null, plays: 0}]}}}).status, 400);
assert.equal(call('alice', 'POST', '/import', {...poc, films: {'FILMPOC-1': {...watched, history_export_dates: ['2026-02-30']}}}).status, 400);
assert.equal(users.alice.extensionProperties.filmMovarySnapshot, old);
const bobInput = {...real};
assert.equal(call('bob', 'POST', '/import', bobInput).status, 200);
assert.deepEqual(Object.keys(call('bob', 'GET', '/watched', {project: 'FILMREAL'}).value.films), ['FILMREAL-1']);
visible = false;
assert.deepEqual(Object.keys(call('alice', 'GET', '/watched', {project: 'FILMPOC'}).value.films), []);
assert.deepEqual(Object.keys(call('alice', 'GET', '/watched', {project: 'FILMREAL'}).value.films), ['FILMREAL-1']);
assert.equal(call('alice', 'POST', '/import', poc).status, 404);
assert.equal(users.alice.extensionProperties.filmMovarySnapshot, old);
users.bob.extensionProperties.filmMovarySnapshot = 'malformed';
assert.equal(call('bob', 'POST', '/import', bobInput).status, 500);
assert.equal(users.bob.extensionProperties.filmMovarySnapshot, 'malformed');
visible = true;
// Migrate the existing v1 mixed-project store without discarding either group.
const {project, ...v1} = poc;
v1.films = {'FILMPOC-1': watched, 'FILMREAL-1': watched};
users.legacy.extensionProperties.filmMovarySnapshot = JSON.stringify(v1);
assert.deepEqual(call('legacy', 'GET', '/watched', {project: 'FILMPOC'}).value.films, poc.films);
assert.deepEqual(call('legacy', 'GET', '/watched', {project: 'FILMREAL'}).value.films, real.films);
assert.equal(call('legacy', 'POST', '/import', {...real, observed_at: '2026-11-06T12:00:00Z'}).status, 200);
assert.deepEqual(call('legacy', 'GET', '/watched', {project: 'FILMPOC'}).value.films, poc.films);
// Empty v1 data has no project identity and is retained without inventing one.
users.empty.extensionProperties.filmMovarySnapshot = JSON.stringify({...v1, films: {}});
assert.equal(call('empty', 'GET', '/watched', {project: 'FILMREAL'}).value.status, 'unknown');
assert.equal(call('empty', 'POST', '/import', real).status, 200);
assert.deepEqual(JSON.parse(users.empty.extensionProperties.filmMovarySnapshot).legacy_empty, {...v1, films: {}});
assert.equal(call('empty', 'POST', '/import', poc).status, 200);
assert.deepEqual(JSON.parse(users.empty.extensionProperties.filmMovarySnapshot).legacy_empty, {...v1, films: {}});
assert.deepEqual(call('empty', 'GET', '/watched', {project: 'FILMREAL'}).value.films, real.films);
console.log('Synthetic Movary snapshot validation, isolation, repeats, and visibility checks passed');
