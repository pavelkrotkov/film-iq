/* Imports only a caller-supplied Movary watched snapshot; never writes Movary. */
const entities = require('@jetbrains/youtrack-scripting-api/entities');
const VERSION = 'youtrack-poc-movary-watched-v1';

function allowedUser(ctx) {
  return ctx.currentUser && ctx.currentUser.login !== 'guest' && !ctx.currentUser.isBanned;
}

function visible(ctx, issueId) {
  if (typeof issueId !== 'string' || !/^(FILMPOC|FILMREAL)-[1-9]\d*$/.test(issueId)) return false;
  const issue = entities.Issue.findById(issueId);
  return !!(issue && issue.project && ['FILMPOC', 'FILMREAL'].includes(issue.project.key) &&
    issueId.startsWith(issue.project.key + '-') && issue.isReported && issue.isVisibleTo(ctx.currentUser));
}

function keys(value, expected) {
  return value && typeof value === 'object' && !Array.isArray(value) &&
    Object.keys(value).sort().join(',') === expected;
}

function date(value) {
  if (value === null) return true;
  if (typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;
  const moment = new Date(value + 'T00:00:00.000Z');
  return Number.isFinite(moment.getTime()) && moment.toISOString().slice(0, 10) === value;
}

function observed(value) {
  if (typeof value !== 'string' ||
      !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-]\d{2}:\d{2})$/.test(value) ||
      !date(value.slice(0, 10))) return false;
  return Number.isFinite(Date.parse(value));
}

function snapshot(value) {
  if (!keys(value, 'complete,films,observed_at,source,version') || value.version !== VERSION ||
      value.source !== 'Movary' || value.complete !== true || !observed(value.observed_at) ||
      !value.films || typeof value.films !== 'object' || Array.isArray(value.films)) {
    throw new Error('Invalid watched snapshot');
  }
  for (const id of Object.keys(value.films)) {
    const film = value.films[id];
    if (!keys(film, 'history_export_dates,played_watch_dates,watched') || film.watched !== true ||
        !Array.isArray(film.history_export_dates) || !film.history_export_dates.every(date) ||
        !Array.isArray(film.played_watch_dates) || !film.played_watch_dates.every(event =>
          keys(event, 'date,plays') && date(event.date) && Number.isSafeInteger(event.plays) && event.plays > 0)) {
      throw new Error('Invalid watched film');
    }
  }
  return value;
}

function error(ctx, code, message) { ctx.response.code = code; ctx.response.json({error: message}); }

exports.httpHandler = {
  endpoints: [
    {
      scope: 'global', method: 'GET', path: '/watched',
      handle: function(ctx) {
        if (!allowedUser(ctx)) return error(ctx, 401, 'Sign-in required');
        try {
          const raw = ctx.currentUser.extensionProperties.filmMovarySnapshot;
          if (!raw) return ctx.response.json({status: 'unknown', source: 'Movary', observed_at: null, films: {}});
          const saved = snapshot(JSON.parse(raw));
          const films = {};
          for (const id of Object.keys(saved.films)) if (visible(ctx, id)) films[id] = saved.films[id];
          ctx.response.json({status: 'available', source: saved.source, observed_at: saved.observed_at, films});
        } catch (_) { error(ctx, 500, 'Watched snapshot unavailable'); }
      }
    },
    {
      scope: 'global', method: 'POST', path: '/import',
      handle: function(ctx) {
        if (!allowedUser(ctx)) return error(ctx, 401, 'Sign-in required');
        let proposed;
        try { proposed = snapshot(ctx.request.json()); }
        catch (_) { return error(ctx, 400, 'Invalid watched snapshot'); }
        try {
          for (const id of Object.keys(proposed.films)) {
            if (!visible(ctx, id)) return error(ctx, 404, 'One or more films are unavailable');
          }
        } catch (_) { return error(ctx, 500, 'Film visibility could not be checked'); }
        // Validate every row and check access before the single property write.
        ctx.currentUser.extensionProperties.filmMovarySnapshot = JSON.stringify(proposed);
        ctx.response.json({status: 'imported', films: Object.keys(proposed.films).length});
      }
    }
  ]
};
