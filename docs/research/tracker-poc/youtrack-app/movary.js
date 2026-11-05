/* Imports only a caller-supplied Movary watched snapshot; never writes Movary. */
const entities = require('@jetbrains/youtrack-scripting-api/entities');
const VERSION = 'youtrack-poc-movary-watched-v1';
const STORE_VERSION = 'youtrack-poc-movary-projects-v2';
const PROJECTS = ['FILMPOC', 'FILMREAL'];

function allowedUser(ctx) {
  return ctx.currentUser && ctx.currentUser.login !== 'guest' && !ctx.currentUser.isBanned;
}

function visible(ctx, project, issueId) {
  if (!PROJECTS.includes(project) || typeof issueId !== 'string' ||
      !/^(FILMPOC|FILMREAL)-[1-9]\d*$/.test(issueId) || !issueId.startsWith(project + '-')) return false;
  const issue = entities.Issue.findById(issueId);
  return !!(issue && issue.project && issue.project.key === project && issue.isReported &&
    issue.isVisibleTo(ctx.currentUser));
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

function older(left, right) {
  const milliseconds = Date.parse(left) - Date.parse(right);
  if (milliseconds !== 0) return milliseconds < 0;
  // Date.parse truncates beyond milliseconds; Movary refreshes can contain microseconds.
  const tail = value => Number(((value.match(/\.(\d{1,6})(?:Z|[+-]\d{2}:\d{2})$/) || [,''])[1] + '000000').slice(3, 6));
  return tail(left) < tail(right);
}

function snapshot(value, legacy = false) {
  const expected = legacy ? 'complete,films,observed_at,source,version' : 'complete,films,observed_at,project,source,version';
  if (!keys(value, expected) || value.version !== VERSION ||
      value.source !== 'Movary' || value.complete !== true || !observed(value.observed_at) ||
      (!legacy && !PROJECTS.includes(value.project)) ||
      !value.films || typeof value.films !== 'object' || Array.isArray(value.films)) {
    throw new Error('Invalid watched snapshot');
  }
  for (const id of Object.keys(value.films)) {
    const film = value.films[id];
    if (!/^(FILMPOC|FILMREAL)-[1-9]\d*$/.test(id) || (!legacy && !id.startsWith(value.project + '-')) ||
        !keys(film, 'history_export_dates,played_watch_dates,watched') || film.watched !== true ||
        !Array.isArray(film.history_export_dates) || !film.history_export_dates.every(date) ||
        !Array.isArray(film.played_watch_dates) || !film.played_watch_dates.every(event =>
          keys(event, 'date,plays') && date(event.date) && Number.isSafeInteger(event.plays) && event.plays > 0)) {
      throw new Error('Invalid watched film');
    }
  }
  return value;
}

function stored(raw) {
  if (!raw) return {version: STORE_VERSION, projects: {}, legacy_empty: null};
  const value = JSON.parse(raw);
  if (value && value.version === VERSION && !Object.prototype.hasOwnProperty.call(value, 'project')) {
    const previous = snapshot(value, true);
    const projects = {};
    for (const id of Object.keys(previous.films)) {
      const project = id.split('-')[0];
      if (!projects[project]) projects[project] = {...previous, project, films: {}};
      projects[project].films[id] = previous.films[id];
    }
    // An empty legacy snapshot has no project identity; preserve it without guessing.
    return {version: STORE_VERSION, projects, legacy_empty: Object.keys(previous.films).length ? null : previous};
  }
  if (!keys(value, 'legacy_empty,projects,version') || value.version !== STORE_VERSION ||
      !value.projects || typeof value.projects !== 'object' || Array.isArray(value.projects)) {
    throw new Error('Invalid stored snapshots');
  }
  if (value.legacy_empty !== null && Object.keys(snapshot(value.legacy_empty, true).films).length) {
    throw new Error('Invalid unscoped snapshot');
  }
  for (const project of Object.keys(value.projects)) {
    if (!PROJECTS.includes(project) || snapshot(value.projects[project]).project !== project) {
      throw new Error('Invalid stored project');
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
        const project = ctx.request.getParameter('project');
        if (!PROJECTS.includes(project)) return error(ctx, 400, 'Project is required');
        try {
          const raw = ctx.currentUser.extensionProperties.filmMovarySnapshot;
          const saved = stored(raw).projects[project];
          if (!saved) return ctx.response.json({status: 'unknown', source: 'Movary', observed_at: null, films: {}});
          const films = {};
          for (const id of Object.keys(saved.films)) if (visible(ctx, project, id)) films[id] = saved.films[id];
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
            if (!visible(ctx, proposed.project, id)) return error(ctx, 404, 'One or more films are unavailable');
          }
        } catch (_) { return error(ctx, 500, 'Film visibility could not be checked'); }
        let current;
        try {
          const raw = ctx.currentUser.extensionProperties.filmMovarySnapshot;
          current = stored(raw);
          const previous = current.projects[proposed.project];
          if (previous && older(proposed.observed_at, previous.observed_at)) {
            return error(ctx, 409, 'A newer watched snapshot already exists');
          }
        } catch (_) { return error(ctx, 500, 'Stored watched snapshot unavailable'); }
        // Validate every row and check access before the single property write.
        current.projects[proposed.project] = proposed;
        ctx.currentUser.extensionProperties.filmMovarySnapshot = JSON.stringify(current);
        ctx.response.json({status: 'imported', films: Object.keys(proposed.films).length});
      }
    }
  ]
};
