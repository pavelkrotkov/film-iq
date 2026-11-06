/* Imports only a caller-supplied Movary watched snapshot; never writes Movary. */
const entities = require('@jetbrains/youtrack-scripting-api/entities');
const VERSION = 'youtrack-poc-movary-watched-v1';
const BOUND_VERSION = 'youtrack-poc-movary-watched-v2';
const REFRESH_VERSION = 'youtrack-poc-movary-watched-v3';
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

function sameObservationEntries(previous, proposed) {
  const oldKeys = Object.keys(previous.films).sort();
  const newKeys = Object.keys(proposed.films).sort();
  if (JSON.stringify(oldKeys) !== JSON.stringify(newKeys)) return false;
  const events = film => JSON.stringify([film.watched, film.history_export_dates,
    film.played_watch_dates.map(event => [event.date, event.plays])]);
  return oldKeys.every(id => {
    const before = previous.films[id], after = proposed.films[id];
    return events(before) === events(after) &&
      (!Object.prototype.hasOwnProperty.call(before, 'tmdb_id') || before.tmdb_id === after.tmdb_id);
  });
}

function filmValid(film, bound, allowNull, identities) {
  if (!keys(film, bound ? 'history_export_dates,played_watch_dates,tmdb_id,watched' : 'history_export_dates,played_watch_dates,watched') ||
      film.watched !== true ||
      (bound && ((film.tmdb_id === null && !allowNull) ||
        (film.tmdb_id !== null && (!Number.isSafeInteger(film.tmdb_id) || film.tmdb_id <= 0 || film.tmdb_id > 2147483647 || identities.has(film.tmdb_id))))) ||
      !Array.isArray(film.history_export_dates) || !film.history_export_dates.every(date) ||
      !Array.isArray(film.played_watch_dates) || !film.played_watch_dates.every(event =>
        keys(event, 'date,plays') && date(event.date) && Number.isSafeInteger(event.plays) && event.plays > 0)) return false;
  if (bound && film.tmdb_id !== null) identities.add(film.tmdb_id);
  return true;
}

function snapshot(value, legacy = false) {
  const expected = legacy ? 'complete,films,observed_at,source,version' :
    value && value.version === REFRESH_VERSION ? 'complete,films,historical,observed_at,project,source,version' : 'complete,films,observed_at,project,source,version';
  if (!keys(value, expected) || ![VERSION, BOUND_VERSION, REFRESH_VERSION].includes(value.version) || (legacy && value.version !== VERSION) ||
      value.source !== 'Movary' || value.complete !== true || !observed(value.observed_at) ||
      (!legacy && !PROJECTS.includes(value.project)) ||
      !value.films || typeof value.films !== 'object' || Array.isArray(value.films)) {
    throw new Error('Invalid watched snapshot');
  }
  const identities = new Set();
  for (const id of Object.keys(value.films)) {
    const film = value.films[id];
    const bound = value.version !== VERSION;
    if (!/^(FILMPOC|FILMREAL)-[1-9]\d*$/.test(id) || (!legacy && !id.startsWith(value.project + '-')) ||
        !filmValid(film, bound, value.version === BOUND_VERSION, identities)) {
      throw new Error('Invalid watched film');
    }
  }
  if (value.version === REFRESH_VERSION && (!Array.isArray(value.historical) || !value.historical.every(item =>
    keys(item, 'film,issue_id,observed_at,reason') && typeof item.issue_id === 'string' &&
    /^(FILMPOC|FILMREAL)-[1-9]\d*$/.test(item.issue_id) && item.issue_id.startsWith(value.project + '-') &&
    observed(item.observed_at) && !older(value.observed_at, item.observed_at) &&
    ['unbound','superseded'].includes(item.reason) && filmValid(item.film, true, true, new Set()) &&
    ((item.reason === 'unbound') === (item.film.tmdb_id === null))))) throw new Error('Invalid historical evidence');
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
          const result = {status: 'available', source: saved.source, observed_at: saved.observed_at, films};
          if (saved.version === REFRESH_VERSION) result.historical = saved.historical.filter(item => visible(ctx, project, item.issue_id));
          ctx.response.json(result);
        } catch (_) { error(ctx, 500, 'Watched snapshot unavailable'); }
      }
    },
    {
      scope: 'global', method: 'POST', path: '/import',
      handle: function(ctx) {
        if (!allowedUser(ctx)) return error(ctx, 401, 'Sign-in required');
        let proposed;
        try { proposed = snapshot(ctx.request.json()); if (proposed.version === REFRESH_VERSION) throw new Error('Use refresh'); }
        catch (_) { return error(ctx, 400, 'Invalid watched snapshot'); }
        try {
          for (const id of Object.keys(proposed.films)) {
            if (!visible(ctx, proposed.project, id)) return error(ctx, 404, 'One or more films are unavailable');
            if (proposed.version === BOUND_VERSION && proposed.films[id].tmdb_id !== null && entities.Issue.findById(id).fields['FilmIQ TMDB ID'] !== proposed.films[id].tmdb_id) {
              return error(ctx, 409, 'A supplied film identity no longer matches its issue');
            }
          }
        } catch (_) { return error(ctx, 500, 'Film visibility could not be checked'); }
        let current;
        try {
          const raw = ctx.currentUser.extensionProperties.filmMovarySnapshot;
          current = stored(raw);
          const previous = current.projects[proposed.project];
          if (previous && Object.keys(previous.films).some(id => !visible(ctx, proposed.project, id))) {
            return error(ctx, 409, 'Existing watched entries are unavailable; no snapshot was replaced');
          }
          if (previous && older(proposed.observed_at, previous.observed_at)) {
            return error(ctx, 409, 'A newer watched snapshot already exists');
          }
          if (previous && (previous.version === REFRESH_VERSION || older(previous.observed_at, proposed.observed_at))) {
            return error(ctx, 409, 'Use the guarded refresh for a newer observation');
          }
          if (previous && !older(previous.observed_at, proposed.observed_at) && !older(proposed.observed_at, previous.observed_at) &&
              !sameObservationEntries(previous, proposed)) {
            return error(ctx, 409, 'Same-observation watched mapping differs; no snapshot was replaced');
          }
        } catch (_) { return error(ctx, 500, 'Stored watched snapshot unavailable'); }
        // Validate every row and check access before the single property write.
        current.projects[proposed.project] = proposed;
        ctx.currentUser.extensionProperties.filmMovarySnapshot = JSON.stringify(current);
        ctx.response.json({status: 'imported', films: Object.keys(proposed.films).length});
      }
    },
    {
      scope: 'global', method: 'POST', path: '/refresh',
      handle: function(ctx) {
        if (!allowedUser(ctx)) return error(ctx, 401, 'Sign-in required');
        let proposed, current, previous;
        try {
          const input = ctx.request.json();
          if (!keys(input, 'complete,films,observed_at,project,source,version') || input.version !== REFRESH_VERSION) throw new Error('Invalid refresh');
          proposed = snapshot({...input, historical: []});
        } catch (_) { return error(ctx, 400, 'Invalid watched refresh'); }
        try {
          current = stored(ctx.currentUser.extensionProperties.filmMovarySnapshot);
          previous = current.projects[proposed.project];
          if (previous) {
            const ids = [...Object.keys(previous.films), ...(previous.historical || []).map(item => item.issue_id)];
            if (ids.some(id => !visible(ctx, proposed.project, id))) return error(ctx, 409, 'Existing watched entries are unavailable; no snapshot was replaced');
          }
          for (const id of Object.keys(proposed.films)) {
            if (!visible(ctx, proposed.project, id)) return error(ctx, 404, 'One or more films are unavailable');
            if (entities.Issue.findById(id).fields['FilmIQ TMDB ID'] !== proposed.films[id].tmdb_id) return error(ctx, 409, 'A supplied film identity no longer matches its issue');
          }
          if (previous && !older(previous.observed_at, proposed.observed_at)) {
            if (previous.version === REFRESH_VERSION && !older(proposed.observed_at, previous.observed_at) && sameObservationEntries(previous, proposed)) {
              return ctx.response.json({status: 'unchanged', films: Object.keys(previous.films).length});
            }
            return error(ctx, 409, 'A newer watched observation is required');
          }
          const historical = previous && previous.version === REFRESH_VERSION ? previous.historical.slice() : [];
          if (previous) for (const id of Object.keys(previous.films)) {
            const old = previous.films[id], next = proposed.films[id];
            const oldId = Object.prototype.hasOwnProperty.call(old, 'tmdb_id') ? old.tmdb_id : null;
            const oldFilm = {watched: old.watched, tmdb_id: oldId, played_watch_dates: old.played_watch_dates, history_export_dates: old.history_export_dates};
            const same = oldId !== null && next && oldId === next.tmdb_id &&
              JSON.stringify([old.played_watch_dates.map(event => [event.date, event.plays]), old.history_export_dates]) ===
              JSON.stringify([next.played_watch_dates.map(event => [event.date, event.plays]), next.history_export_dates]);
            if (!same) historical.push({issue_id: id, observed_at: previous.observed_at, reason: oldId === null ? 'unbound' : 'superseded', film: oldFilm});
          }
          proposed.historical = historical;
          snapshot(proposed);
        } catch (_) { return error(ctx, 500, 'Stored watched snapshot unavailable'); }
        current.projects[proposed.project] = proposed;
        ctx.currentUser.extensionProperties.filmMovarySnapshot = JSON.stringify(current);
        ctx.response.json({status: 'imported', films: Object.keys(proposed.films).length});
      }
    },
    {
      scope: 'global', method: 'POST', path: '/restore-legacy',
      handle: function(ctx) {
        if (!allowedUser(ctx)) return error(ctx, 401, 'Sign-in required');
        let request, current;
        try {
          request = ctx.request.json();
          if (!keys(request, 'project') || !PROJECTS.includes(request.project)) return error(ctx, 400, 'Project is required');
          current = stored(ctx.currentUser.extensionProperties.filmMovarySnapshot);
          const previous = current.projects[request.project];
          if (!previous) return error(ctx, 404, 'Watched snapshot unavailable');
          if (Object.keys(previous.films).some(id => !visible(ctx, request.project, id))) {
            return error(ctx, 409, 'Existing watched entries are unavailable; no snapshot was replaced');
          }
          if (previous.version === VERSION) return ctx.response.json({status: 'already-legacy', films: Object.keys(previous.films).length});
          if (previous.version === REFRESH_VERSION && previous.historical.length) return error(ctx, 409, 'Historical evidence cannot be represented by the legacy format');
          const films = {};
          for (const id of Object.keys(previous.films)) {
            const film = previous.films[id];
            films[id] = {watched: film.watched, played_watch_dates: film.played_watch_dates, history_export_dates: film.history_export_dates};
          }
          const {historical, ...legacy} = previous;
          current.projects[request.project] = {...legacy, version: VERSION, films};
        } catch (_) { return error(ctx, 500, 'Stored watched snapshot unavailable'); }
        ctx.currentUser.extensionProperties.filmMovarySnapshot = JSON.stringify(current);
        ctx.response.json({status: 'restored', films: Object.keys(current.projects[request.project].films).length});
      }
    }
  ]
};
