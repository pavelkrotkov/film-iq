/* Read-only Movary watchlist observations for the current user and project. */
const entities = require('@jetbrains/youtrack-scripting-api/entities');
const SNAPSHOT = 'tracker-poc-movary-watchlist-v1';
const STORE = 'youtrack-poc-movary-watchlists-v1';
const EXPORT = 'filmiq-watchlist-property-export-v1';
const PROJECTS = ['FILMPOC', 'FILMREAL'];

function keys(value, expected) {
  return value && typeof value === 'object' && !Array.isArray(value) &&
    Object.keys(value).sort().join(',') === expected;
}
function allowedUser(ctx) {
  return ctx.currentUser && ctx.currentUser.login !== 'guest' && !ctx.currentUser.isBanned;
}
function projectVisible(ctx, key) {
  if (!PROJECTS.includes(key)) return false;
  const project = entities.Project.findByKey(key);
  return !!(project && project.key === key && ctx.currentUser.hasPermission('READ_ISSUE', project));
}
function date(value) {
  if (typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;
  const parsed = new Date(value + 'T00:00:00.000Z');
  return Number.isFinite(parsed.getTime()) && parsed.toISOString().slice(0, 10) === value;
}
function timestamp(value, requireZone) {
  if (typeof value !== 'string') return false;
  const match = value.match(/^(\d{4}-\d{2}-\d{2})(?:[T ](\d{2}):(\d{2})(?::(\d{2})(?:\.\d{1,6})?)?(Z|[+-]\d{2}:\d{2})?)?$/);
  if (!match || !date(match[1])) return false;
  if (requireZone && (!match[2] || !match[5])) return false;
  if (match[2] && (Number(match[2]) > 23 || Number(match[3]) > 59 || Number(match[4] || 0) > 59)) return false;
  return Number.isFinite(Date.parse(value.replace(' ', 'T')));
}
function older(left, right) {
  const ms = Date.parse(left) - Date.parse(right);
  if (ms !== 0) return ms < 0;
  const tail = value => Number(((value.match(/\.(\d{1,6})(?:Z|[+-]\d{2}:\d{2})$/) || [,''])[1] + '000000').slice(3, 6));
  return tail(left) < tail(right);
}
function snapshot(value) {
  if (!keys(value, 'entries,observed_at,project,source,version') || value.version !== SNAPSHOT ||
      value.source !== 'Movary' || !PROJECTS.includes(value.project) ||
      !timestamp(value.observed_at, true) || !Array.isArray(value.entries)) throw new Error('Invalid snapshot');
  const seen = new Set();
  for (const entry of value.entries) {
    if (!keys(entry, 'added_at,title,tmdb_id') || !Number.isSafeInteger(entry.tmdb_id) ||
        entry.tmdb_id <= 0 || entry.tmdb_id > 2147483647 || seen.has(entry.tmdb_id) ||
        !(entry.title === null || typeof entry.title === 'string' && entry.title.trim()) ||
        !(entry.added_at === null || timestamp(entry.added_at, false))) throw new Error('Invalid entry');
    seen.add(entry.tmdb_id);
  }
  return value;
}
function stored(raw) {
  if (raw === null || raw === '') return {version: STORE, projects: {}};
  if (typeof raw !== 'string') throw new Error('Invalid property');
  const value = JSON.parse(raw);
  if (!keys(value, 'projects,version') || value.version !== STORE || !value.projects ||
      typeof value.projects !== 'object' || Array.isArray(value.projects)) throw new Error('Invalid store');
  for (const key of Object.keys(value.projects)) if (snapshot(value.projects[key]).project !== key) throw new Error('Invalid project');
  return value;
}
function raw(ctx) {
  const value = ctx.currentUser.extensionProperties.filmMovaryWatchlist;
  if (value === null || value === undefined) return null;
  if (typeof value !== 'string') throw new Error('Invalid property');
  return value;
}
function owner(ctx) {
  const user = ctx.currentUser;
  if (typeof user.login !== 'string' || !user.login || typeof user.ringId !== 'string' || !user.ringId) throw new Error('Missing owner');
  return {login: user.login, ring_id: user.ringId};
}
function exportValid(value, user) {
  return keys(value, 'owner,raw,version') && value.version === EXPORT && keys(value.owner, 'login,ring_id') &&
    value.owner.login === user.login && value.owner.ring_id === user.ring_id &&
    (value.raw === null || typeof value.raw === 'string');
}
function accessible(ctx, value) {
  return Object.keys(stored(value).projects).every(project => projectVisible(ctx, project));
}
function fail(ctx, code, message) { ctx.response.code = code; ctx.response.json({error: message}); }

exports.httpHandler = {endpoints: [
  {scope: 'global', method: 'GET', path: '/list', handle: function(ctx) {
    ctx.response.addHeader('Cache-Control', 'no-store');
    if (!allowedUser(ctx)) return fail(ctx, 401, 'Sign-in required');
    const project = ctx.request.getParameter('project');
    if (!PROJECTS.includes(project)) return fail(ctx, 400, 'Project is required');
    try {
      if (!projectVisible(ctx, project)) return fail(ctx, 404, 'Project unavailable');
      const saved = stored(raw(ctx)).projects[project];
      return ctx.response.json(saved ? {status: 'available', source: 'Movary', observed_at: saved.observed_at, entries: saved.entries} :
        {status: 'unknown', source: 'Movary', observed_at: null, entries: []});
    } catch (_) { return fail(ctx, 500, 'Watchlist snapshot unavailable'); }
  }},
  {scope: 'global', method: 'GET', path: '/property-export', handle: function(ctx) {
    ctx.response.addHeader('Cache-Control', 'no-store');
    if (!allowedUser(ctx)) return fail(ctx, 401, 'Sign-in required');
    try {
      const user = owner(ctx), current = raw(ctx);
      if (!accessible(ctx, current)) return fail(ctx, 409, 'Stored project unavailable');
      return ctx.response.json({version: EXPORT, owner: user, raw: current});
    } catch (_) { return fail(ctx, 500, 'Watchlist property unavailable'); }
  }},
  {scope: 'global', method: 'POST', path: '/import', handle: function(ctx) {
    ctx.response.addHeader('Cache-Control', 'no-store');
    if (!allowedUser(ctx)) return fail(ctx, 401, 'Sign-in required');
    let input, user, proposed, current, state;
    try {
      input = ctx.request.json(); user = owner(ctx);
      if (!keys(input, 'expected,owner,snapshot') || !keys(input.owner, 'login,ring_id') ||
          input.owner.login !== user.login || input.owner.ring_id !== user.ring_id ||
          !(input.expected === null || typeof input.expected === 'string')) throw new Error('Invalid import');
      proposed = snapshot(input.snapshot);
    } catch (_) { return fail(ctx, 400, 'Invalid watchlist import'); }
    try {
      current = raw(ctx); state = stored(current);
      if (!projectVisible(ctx, proposed.project) || !accessible(ctx, current)) return fail(ctx, 404, 'Project unavailable');
      if (current !== input.expected) return fail(ctx, 409, 'Watchlist property changed');
      const previous = state.projects[proposed.project];
      if (previous && older(proposed.observed_at, previous.observed_at)) return fail(ctx, 409, 'A newer observation exists');
      if (previous && !older(previous.observed_at, proposed.observed_at) && !older(proposed.observed_at, previous.observed_at)) {
        if (JSON.stringify(previous) === JSON.stringify(proposed)) return ctx.response.json({status: 'unchanged', entries: proposed.entries.length});
        return fail(ctx, 409, 'The same observation differs');
      }
      state.projects[proposed.project] = proposed;
      ctx.currentUser.extensionProperties.filmMovaryWatchlist = JSON.stringify(state);
      return ctx.response.json({status: 'imported', entries: proposed.entries.length});
    } catch (_) { return fail(ctx, 500, 'Watchlist property unavailable'); }
  }},
  {scope: 'global', method: 'POST', path: '/property-restore', handle: function(ctx) {
    ctx.response.addHeader('Cache-Control', 'no-store');
    if (!allowedUser(ctx)) return fail(ctx, 401, 'Sign-in required');
    let input, user, current;
    try {
      input = ctx.request.json(); user = owner(ctx);
      if (!keys(input, 'backup,expected') || !exportValid(input.expected, user) || !exportValid(input.backup, user)) return fail(ctx, 400, 'Invalid restore');
      current = raw(ctx);
      if (!accessible(ctx, current) || !accessible(ctx, input.expected.raw) || !accessible(ctx, input.backup.raw)) return fail(ctx, 409, 'Stored project unavailable');
    } catch (_) { return fail(ctx, 409, 'Watchlist property could not be validated'); }
    if (current !== input.expected.raw) return fail(ctx, 409, 'Watchlist property changed');
    if (current === input.backup.raw) return ctx.response.json({status: 'unchanged'});
    ctx.currentUser.extensionProperties.filmMovaryWatchlist = input.backup.raw;
    return ctx.response.json({status: 'restored'});
  }}
]};
