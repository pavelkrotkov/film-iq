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
const users = Object.fromEntries(['alice', 'bob', 'guest'].map(login => [login, {
  login, isBanned: false, extensionProperties: {filmPreferences: 'unchanged'},
}]));

function call(user, method, endpoint, input) {
  const ctx = {
    currentUser: users[user], request: {json: () => input},
    response: {code: 200, json(value) { this.value = value; }},
  };
  endpoints.find(item => item.method === method && item.path === endpoint).handle(ctx);
  return JSON.parse(JSON.stringify({status: ctx.response.code, value: ctx.response.value}));
}

const watched = {watched: true, played_watch_dates: [{date: null, plays: 2}, {date: '2026-01-05', plays: 3}],
  history_export_dates: [null, '2026-01-05', '2026-01-05']};
const input = {version: 'youtrack-poc-movary-watched-v1', source: 'Movary', complete: true,
  observed_at: '2026-11-05T12:00:00+00:00', films: {'FILMPOC-1': watched, 'FILMREAL-1': watched}};
assert.deepEqual(call('alice', 'GET', '/watched').value,
  {status: 'unknown', source: 'Movary', observed_at: null, films: {}});
assert.equal(call('guest', 'GET', '/watched').status, 401);
assert.equal(call('alice', 'POST', '/import', input).status, 200);
assert.deepEqual(call('alice', 'GET', '/watched').value.films, input.films);
assert.deepEqual(call('bob', 'GET', '/watched').value.films, {});
assert.equal(users.alice.extensionProperties.filmPreferences, 'unchanged');
const old = users.alice.extensionProperties.filmMovarySnapshot;
assert.equal(call('alice', 'POST', '/import', {...input, films: {...input.films, 'OTHER-1': watched}}).status, 404);
assert.equal(call('alice', 'POST', '/import', {...input, films: {...input.films, 'FILMPOC-404': watched}}).status, 404);
assert.equal(call('alice', 'POST', '/import', {...input, films: {'FILMPOC-1': {...watched, personal_notes: 'bad'}}}).status, 400);
assert.equal(call('alice', 'POST', '/import', {...input, films: {'FILMPOC-1': {...watched, played_watch_dates: [{date: null, plays: 0}]}}}).status, 400);
assert.equal(call('alice', 'POST', '/import', {...input, films: {'FILMPOC-1': {...watched, history_export_dates: ['2026-02-30']}}}).status, 400);
assert.equal(users.alice.extensionProperties.filmMovarySnapshot, old);
const bobInput = {...input, films: {'FILMREAL-1': watched}};
assert.equal(call('bob', 'POST', '/import', bobInput).status, 200);
assert.deepEqual(Object.keys(call('bob', 'GET', '/watched').value.films), ['FILMREAL-1']);
visible = false;
assert.deepEqual(Object.keys(call('alice', 'GET', '/watched').value.films), ['FILMREAL-1']);
assert.equal(call('alice', 'POST', '/import', input).status, 404);
assert.equal(users.alice.extensionProperties.filmMovarySnapshot, old);
console.log('Synthetic Movary snapshot validation, isolation, repeats, and visibility checks passed');
