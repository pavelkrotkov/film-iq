/* Isolated synthetic experiment: no live film IDs or provider credentials. */
const entities = require('@jetbrains/youtrack-scripting-api/entities');
const http = require('@jetbrains/youtrack-scripting-api/http');
const APPROVED_FIXTURE_IDS = new Set([900000001, 900000002]);

function reply(ctx, code, value) {
  ctx.response.code = code;
  ctx.response.addHeader('Cache-Control', 'no-store');
  ctx.response.json(value);
}

exports.httpHandler = {
  endpoints: [{
    scope: 'issue', method: 'POST', path: '/read',
    handle: function(ctx) {
      const issue = ctx.issue, user = ctx.currentUser;
      if (!user || user.login === 'guest' || user.isBanned) return reply(ctx, 401, {error: 'Sign-in required'});
      if (!issue || !issue.project || issue.project.key !== 'FILMPOC' || !issue.isReported || !issue.isVisibleTo(user)) {
        return reply(ctx, 404, {error: 'Film unavailable'});
      }
      const id = issue.fields['FilmIQ TMDB ID'];
      if (!Number.isSafeInteger(id) || !APPROVED_FIXTURE_IDS.has(id)) return reply(ctx, 403, {error: 'Fixture ID not approved'});
      const url = ctx.settings.bridgeUrl;
      if (typeof url !== 'string' || !/^http:\/\/127\.0\.0\.1:[1-9][0-9]{0,4}$/.test(url)) return reply(ctx, 503, {error: 'Fixture bridge unavailable'});
      try {
        const connection = new http.Connection(url);
        connection.bearerAuth(ctx.settings.bridgeToken);
        connection.addHeader('Content-Type', 'application/json');
        const response = connection.postSync('/metadata', null, JSON.stringify({tmdb_id: id}));
        if (response.code === 429) return reply(ctx, 429, {error: 'Provider rate limit reached'});
        if (response.code !== 200) return reply(ctx, 502, {error: 'Fixture metadata unavailable'});
        const data = response.json();
        if (!data || data.tmdb_id !== id || typeof data.title !== 'string') return reply(ctx, 502, {error: 'Invalid fixture response'});
        return reply(ctx, 200, data);
      } catch (_) { return reply(ctx, 502, {error: 'Fixture metadata unavailable'}); }
    }
  }],
  requirements: { filmId: { type: entities.Field.integerType, name: 'FilmIQ TMDB ID' } }
};
