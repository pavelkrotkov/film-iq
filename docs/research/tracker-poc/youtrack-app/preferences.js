/* A POC. All access is scoped to the authenticated caller and the named projects. */
const entities = require('@jetbrains/youtrack-scripting-api/entities');

const same = (left, right) => JSON.stringify(left) === JSON.stringify(right);

function preference(value) {
  if (!value || typeof value !== 'object' || Array.isArray(value) ||
      Object.keys(value).sort().join(',') !== 'interest_score,personal_notes,watched_at,watchlist') {
    throw new Error('Invalid preference');
  }
  const score = value.interest_score;
  if (!(score === null || (Number.isInteger(score) && score >= 1 && score <= 10))) {
    throw new Error('Interest must be null or an integer from 1 to 10');
  }
  if (!(value.watchlist === null || typeof value.watchlist === 'boolean') || typeof value.personal_notes !== 'string' ||
      value.personal_notes.length > 10000) {
    throw new Error('Invalid watchlist or notes');
  }
  const watched = value.watched_at;
  if (watched !== null &&
      (typeof watched !== 'string' || !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/.test(watched) ||
       !Number.isFinite(Date.parse(watched)) || new Date(watched).toISOString() !== watched)) {
    throw new Error('Watched time must be null or an ISO UTC timestamp');
  }
  return {interest_score: score, watchlist: value.watchlist, watched_at: watched, personal_notes: value.personal_notes};
}

function issueFor(ctx, issueId) {
  if (!ctx.currentUser || ctx.currentUser.login === 'guest' || ctx.currentUser.isBanned ||
      typeof issueId !== 'string' || !/^(FILMPOC|FILMREAL)-[1-9]\d*$/.test(issueId)) return null;
  const issue = entities.Issue.findById(issueId);
  return issue && issue.project && ['FILMPOC', 'FILMREAL'].includes(issue.project.key) &&
    issueId.startsWith(issue.project.key + '-') &&
    issue.isReported && issue.isVisibleTo(ctx.currentUser) ? issue : null;
}

function store(ctx) {
  const raw = ctx.currentUser.extensionProperties.filmPreferences;
  if (!raw) return {};
  const value = JSON.parse(raw);
  if (!value || typeof value !== 'object' || Array.isArray(value) || value.version !== 1 ||
      !value.items || typeof value.items !== 'object' || Array.isArray(value.items)) {
    throw new Error('Stored preferences are invalid');
  }
  return value.items;
}

function error(ctx, status, message) {
  ctx.response.code = status;
  ctx.response.json({error: message});
}

function read(ctx, issueId) {
  if (!issueFor(ctx, issueId)) return null;
  const items = store(ctx);
  const recorded = Object.prototype.hasOwnProperty.call(items, issueId);
  return {issue_id: issueId, recorded, preference: recorded ? preference(items[issueId]) : null};
}

function body(ctx) {
  try { return ctx.request.json(); } catch (_) { return null; }
}

exports.httpHandler = {
  endpoints: [
    {
      scope: 'global', method: 'GET', path: '/all',
      handle: function(ctx) {
        if (!ctx.currentUser || ctx.currentUser.login === 'guest' || ctx.currentUser.isBanned) {
          return error(ctx, 401, 'Sign-in required');
        }
        try {
          const items = store(ctx), visible = {};
          for (const issueId of Object.keys(items)) {
            if (issueFor(ctx, issueId)) {
              visible[issueId] = {recorded: true, preference: preference(items[issueId])};
            }
          }
          ctx.response.json({preferences: visible});
        } catch (_) { error(ctx, 500, 'Stored preferences unavailable'); }
      }
    },
    {
      scope: 'global', method: 'GET', path: '/preference',
      handle: function(ctx) {
        const issueId = ctx.request.getParameter('issue_id');
        try {
          const result = read(ctx, issueId);
          if (!result) return error(ctx, 404, 'Film unavailable');
          ctx.response.json(result);
        } catch (_) { error(ctx, 500, 'Stored preferences unavailable'); }
      }
    },
    {
      scope: 'global', method: 'POST', path: '/preview',
      handle: function(ctx) {
        const input = body(ctx);
        if (!input || typeof input !== 'object' || Array.isArray(input)) return error(ctx, 400, 'Invalid request');
        try {
          const current = read(ctx, input.issue_id);
          if (!current) return error(ctx, 404, 'Film unavailable');
          let after;
          try { after = preference(input.preference); } catch (_) { return error(ctx, 400, 'Invalid preference'); }
          const preview = {issue_id: current.issue_id, before: current.preference, after};
          ctx.currentUser.extensionProperties.filmPreferencePreview = JSON.stringify(preview);
          ctx.response.json(preview);
        } catch (_) { error(ctx, 500, 'Could not prepare preview'); }
      }
    },
    {
      scope: 'global', method: 'POST', path: '/confirm',
      handle: function(ctx) {
        const input = body(ctx);
        if (!input || typeof input !== 'object' || Array.isArray(input)) return error(ctx, 400, 'Invalid request');
        let current, after, items;
        try {
          current = read(ctx, input.issue_id);
          if (!current) return error(ctx, 404, 'Film unavailable');
          const raw = ctx.currentUser.extensionProperties.filmPreferencePreview;
          const saved = raw ? JSON.parse(raw) : null;
          let before;
          try { before = input.before === null ? null : preference(input.before); after = preference(input.after); }
          catch (_) { return error(ctx, 400, 'Invalid confirmation'); }
          if (!saved || saved.issue_id !== current.issue_id || !same(saved.before, before) ||
              !same(saved.after, after) || !same(current.preference, before)) {
            return error(ctx, 409, 'Preview missing, superseded, or stale');
          }
          items = store(ctx);
        } catch (_) { error(ctx, 500, 'Could not save preferences'); }
        if (!current || !after || !items) return;
        items[current.issue_id] = after;
        // Let write exceptions abort the handler transaction rather than masking them.
        ctx.currentUser.extensionProperties.filmPreferences = JSON.stringify({version: 1, items});
        ctx.currentUser.extensionProperties.filmPreferencePreview = null;
        ctx.response.json({issue_id: current.issue_id, recorded: true, preference: after});
      }
    }
  ]
};
