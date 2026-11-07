/* Run with node; mocks only YouTrack's documented handler context and entities. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const issue = {
  id: 'FILMPOC-1', project: {key: 'FILMPOC'}, isReported: true,
  isVisibleTo: user => user.login !== 'restricted',
};
const differentProject = {...issue, id: 'OTHER-1', project: {key: 'OTHER'}};
const registry = {
  'FILMPOC-1': issue,
  'FILMPOC-2': {...issue, id: 'FILMPOC-2'},
  'FILMPOC-3': {...issue, id: 'FILMPOC-3', isVisibleTo: () => false},
  'FILMREAL-1': {...issue, id: 'FILMREAL-1', project: {key: 'FILMREAL'}},
  'OTHER-1': differentProject,
};
const context = {
  exports: {},
  require(name) {
    assert.equal(name, '@jetbrains/youtrack-scripting-api/entities');
    return {Issue: {findById(id) { return registry[id] || null; }}};
  },
};
vm.runInNewContext(fs.readFileSync(path.join(__dirname, '../preferences.js'), 'utf8'), context);
const endpoints = context.exports.httpHandler.endpoints;
const users = Object.fromEntries(['alice', 'bob', 'restricted', 'guest'].map(login => [login, {
  login, isBanned: false, extensionProperties: {},
}]));

function call(user, method, endpoint, input) {
  const ctx = {
    currentUser: users[user],
    request: {json: () => input, getParameter: key => key === 'issue_id' ? input.issue_id : null},
    response: {code: 200, json(value) { this.value = value; }},
  };
  endpoints.find(item => item.method === method && item.path === endpoint).handle(ctx);
  return JSON.parse(JSON.stringify({status: ctx.response.code, value: ctx.response.value}));
}

const blank = {interest_score: null, watchlist: null, watched_at: null, personal_notes: ''};
const rated = {interest_score: 9, watchlist: true, watched_at: '2026-11-05T12:00:00.000Z', personal_notes: 'Synthetic note'};
assert.deepEqual(call('alice', 'GET', '/preference', {issue_id: issue.id}).value,
  {issue_id: issue.id, recorded: false, preference: null});
assert.equal(call('restricted', 'GET', '/preference', {issue_id: issue.id}).status, 404);
assert.equal(call('guest', 'GET', '/preference', {issue_id: issue.id}).status, 404);
assert.equal(call('alice', 'GET', '/preference', {issue_id: 'OTHER-1'}).status, 404);
assert.equal(call('alice', 'POST', '/preview', {issue_id: issue.id, preference: {...rated, interest_score: 11}}).status, 400);
assert.equal(call('alice', 'POST', '/preview', {issue_id: issue.id, preference: {...rated, watched_at: '2026-02-30T12:00:00.000Z'}}).status, 400);
assert.equal(call('alice', 'POST', '/confirm', {issue_id: issue.id, before: null, after: rated}).status, 409);
const preview = call('alice', 'POST', '/preview', {issue_id: issue.id, preference: rated});
assert.equal(preview.status, 200);
assert.deepEqual(preview.value, {issue_id: issue.id, before: null, after: rated});
assert.equal(users.alice.extensionProperties.filmPreferencePreview.includes(rated.personal_notes), false);
assert.equal(call('alice', 'POST', '/discard', preview.value).status, 200);
assert.equal(users.alice.extensionProperties.filmPreferencePreview, null);
assert.equal(call('alice', 'POST', '/confirm', preview.value).status, 409);
call('alice', 'POST', '/preview', {issue_id: issue.id, preference: rated});
assert.equal(call('bob', 'POST', '/confirm', preview.value).status, 409);
assert.equal(call('alice', 'POST', '/confirm', {...preview.value, before: blank}).status, 409);
assert.equal(call('alice', 'POST', '/confirm', {...preview.value, after: {...rated, watchlist: false}}).status, 409);
assert.equal(call('alice', 'POST', '/confirm', preview.value).status, 200);
assert.deepEqual(call('alice', 'GET', '/preference', {issue_id: issue.id}).value,
  {issue_id: issue.id, recorded: true, preference: rated});
assert.deepEqual(call('bob', 'GET', '/preference', {issue_id: issue.id}).value,
  {issue_id: issue.id, recorded: false, preference: null});
const explicitBlank = call('bob', 'POST', '/preview', {issue_id: issue.id, preference: blank}).value;
assert.equal(call('bob', 'POST', '/confirm', explicitBlank).status, 200);
assert.deepEqual(call('bob', 'GET', '/preference', {issue_id: issue.id}).value,
  {issue_id: issue.id, recorded: true, preference: blank});
assert.equal(call('alice', 'POST', '/confirm', preview.value).status, 409);

const stale = call('alice', 'POST', '/preview', {issue_id: issue.id, preference: blank}).value;
const newPreview = call('alice', 'POST', '/preview', {issue_id: 'FILMPOC-2', preference: rated}).value;
assert.equal(call('alice', 'POST', '/confirm', stale).status, 409);
assert.equal(call('alice', 'POST', '/confirm', newPreview).status, 200);
const filmReal = call('alice', 'POST', '/preview', {issue_id: 'FILMREAL-1', preference: rated}).value;
assert.equal(call('alice', 'POST', '/confirm', filmReal).status, 200);
const withHidden = JSON.parse(users.alice.extensionProperties.filmPreferences);
withHidden.items['FILMPOC-3'] = rated;
withHidden.items['OTHER-1'] = rated;
withHidden.items['FILMPOC-404'] = rated;
users.alice.extensionProperties.filmPreferences = JSON.stringify(withHidden);
const allAlice = call('alice', 'GET', '/all', {}).value.preferences;
assert.deepEqual(Object.keys(allAlice).sort(), ['FILMPOC-1', 'FILMPOC-2', 'FILMREAL-1']);
assert.deepEqual(allAlice['FILMREAL-1'], {recorded: true, preference: rated});
assert.deepEqual(Object.keys(call('bob', 'GET', '/all', {}).value.preferences), ['FILMPOC-1']);
assert.equal(call('guest', 'GET', '/all', {}).status, 401);
const currentChange = call('alice', 'POST', '/preview', {issue_id: issue.id, preference: blank}).value;
const stored = JSON.parse(users.alice.extensionProperties.filmPreferences);
stored.items[issue.id].interest_score = 8;
users.alice.extensionProperties.filmPreferences = JSON.stringify(stored);
assert.equal(call('alice', 'POST', '/confirm', currentChange).status, 409);
const revoked = call('alice', 'POST', '/preview', {issue_id: issue.id, preference: blank}).value;
issue.isVisibleTo = () => false;
assert.equal(call('alice', 'GET', '/preference', {issue_id: issue.id}).status, 404);
assert.equal(call('alice', 'POST', '/confirm', revoked).status, 404);
issue.isVisibleTo = () => true;
users.bob.extensionProperties.filmPreferences = 'malformed';
assert.equal(call('bob', 'POST', '/preview', {issue_id: issue.id, preference: blank}).status, 500);
assert.equal(users.bob.extensionProperties.filmPreferences, 'malformed');
console.log('Synthetic YouTrack preference isolation, visibility, preview and validation checks passed');
