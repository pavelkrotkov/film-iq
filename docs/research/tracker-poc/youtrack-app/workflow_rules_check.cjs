// Deterministic guard/action test; not a YouTrack runtime integration test.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const entities = {
  Issue: {onChange: (rule) => rule, onSchedule: (rule) => rule},
  Field: {integerType: 'integer', stringType: 'string'},
  State: {fieldType: 'state'},
};
function load(file) {
  const exports = {};
  const sandbox = {exports, require(name) {
    if (name === '@jetbrains/youtrack-scripting-api/entities') return entities;
    if (name === '@jetbrains/youtrack-scripting-api/workflow') return {check(ok, message) { if (!ok) throw new Error(message); }};
    throw new Error('Unexpected module');
  }};
  vm.runInNewContext(fs.readFileSync(path.join(__dirname, file), 'utf8'), sandbox);
  return exports.rule;
}
const change = load('poc_lifecycle_guard.js');
const schedule = load('poc_scheduled_marker.js');
let oldState = 'Archived', newState = 'Discovery', changed = true;
const ctx = {
  Lifecycle: {Archived: 'Archived', Discovery: 'Discovery'},
  issue: {
    id: 'FILMPOC-1', project: {key: 'FILMPOC'},
    fields: {
      Fixture: 91001,
      ScheduleMarker: null,
      isChanged: () => changed,
      was: (_, state) => oldState === state,
      becomes: (_, state) => changed && newState === state,
    },
  },
};
assert.equal(change.guard(ctx), true);
assert.throws(() => change.action(ctx), /move Archived to Evaluation/);
newState = 'Evaluation';
assert.doesNotThrow(() => change.action(ctx));
changed = false;
assert.equal(change.guard(ctx), false);
changed = true;
ctx.issue.project.key = 'OTHER';
assert.equal(change.guard(ctx), false);
assert.equal(schedule.guard(ctx), false);
ctx.issue.project.key = 'FILMPOC';
ctx.issue.fields.Fixture = 8;
assert.equal(change.guard(ctx), false);
assert.equal(schedule.guard(ctx), false);
ctx.issue.fields.Fixture = 91001;
assert.equal(schedule.guard(ctx), true);
schedule.action(ctx);
assert.equal(ctx.issue.fields.ScheduleMarker, 'synthetic check processed');
assert.equal(schedule.guard(ctx), false);
assert.equal(schedule.muteUpdateNotifications, true);
console.log('Synthetic lifecycle guard and one-time scheduled marker checks passed');
