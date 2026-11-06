/* Issue identity is resolved server-side; the Python bridge enforces the approved IDs. */
const entities = require('@jetbrains/youtrack-scripting-api/entities');
const http = require('@jetbrains/youtrack-scripting-api/http');
const URL = 'http://127.0.0.1:15178';

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
      if (!issue || !issue.project || !['FILMPOC', 'FILMREAL'].includes(issue.project.key) || !issue.isReported || !issue.isVisibleTo(user)) {
        return reply(ctx, 404, {error: 'Film unavailable'});
      }
      const id = issue.fields['FilmIQ TMDB ID'];
      if (!Number.isSafeInteger(id) || id <= 0 || id > 2147483647) return reply(ctx, 400, {error: 'Film identifier unavailable'});
      try {
        const connection = new http.Connection(URL);
        connection.bearerAuth(ctx.settings.bridgeToken);
        connection.addHeader('Content-Type', 'application/json');
        const response = connection.postSync('/metadata', null, JSON.stringify({tmdb_id: id}));
        if (response.code === 429) return reply(ctx, 429, {error: 'TMDB rate limit reached'});
        if (response.code === 403) return reply(ctx, 403, {error: 'Film not approved'});
        if (response.code === 503) return reply(ctx, 503, {error: 'Live refresh temporarily unavailable'});
        if (response.code !== 200) return reply(ctx, 502, {error: 'TMDB unavailable'});
        const data = response.json();
        if (!data || data.tmdb_id !== id || typeof data.title !== 'string' || !data.availability || !Array.isArray(data.availability.offers)) return reply(ctx, 502, {error: 'Invalid metadata response'});
        return reply(ctx, 200, data);
      } catch (_) { return reply(ctx, 502, {error: 'TMDB unavailable'}); }
    }
  }, {
    scope: 'issue', method: 'GET', path: '/cached',
    handle: function(ctx) {
      const issue = ctx.issue, user = ctx.currentUser;
      if (!user || user.login === 'guest' || user.isBanned) return reply(ctx, 401, {error: 'Sign-in required'});
      if (!issue || !issue.project || !['FILMPOC', 'FILMREAL'].includes(issue.project.key) || !issue.isReported || !issue.isVisibleTo(user)) {
        return reply(ctx, 404, {error: 'Film unavailable'});
      }
      const id = issue.fields['FilmIQ TMDB ID'];
      if (!Number.isSafeInteger(id) || id <= 0 || id > 2147483647) return reply(ctx, 400, {error: 'Film identifier unavailable'});
      try {
        const connection = new http.Connection(URL);
        connection.bearerAuth(ctx.settings.bridgeToken);
        connection.addHeader('Content-Type', 'application/json');
        const response = connection.postSync('/cache', null, JSON.stringify({tmdb_id: id}));
        if (response.code === 404) return reply(ctx, 404, {error: 'Cache miss'});
        if (response.code === 403) return reply(ctx, 403, {error: 'Film not approved'});
        if (response.code !== 200) return reply(ctx, 503, {error: 'Cache unavailable'});
        const data = response.json();
        if (!data || data.tmdb_id !== id || typeof data.title !== 'string' || !data.availability || !Array.isArray(data.availability.offers)) return reply(ctx, 503, {error: 'Invalid cache response'});
        return reply(ctx, 200, data);
      } catch (_) { return reply(ctx, 503, {error: 'Cache unavailable'}); }
    }
  }, {
    scope: 'issue', method: 'GET', path: '/status',
    handle: function(ctx) {
      const issue = ctx.issue, user = ctx.currentUser;
      if (!user || user.login === 'guest' || user.isBanned) return reply(ctx, 401, {error: 'Sign-in required'});
      if (!issue || !issue.project || !['FILMPOC', 'FILMREAL'].includes(issue.project.key) || !issue.isReported || !issue.isVisibleTo(user)) {
        return reply(ctx, 404, {error: 'Film unavailable'});
      }
      const id = issue.fields['FilmIQ TMDB ID'];
      if (!Number.isSafeInteger(id) || id <= 0 || id > 2147483647) return reply(ctx, 400, {error: 'Film identifier unavailable'});
      try {
        const connection = new http.Connection(URL);
        connection.bearerAuth(ctx.settings.bridgeToken);
        connection.addHeader('Content-Type', 'application/json');
        const response = connection.postSync('/status', null, JSON.stringify({tmdb_id: id}));
        if (response.code === 403) return reply(ctx, 403, {error: 'Film not approved'});
        if (response.code !== 200) return reply(ctx, 503, {error: 'Bridge status unavailable'});
        const data = response.json();
        if (!data || typeof data.pace_enabled !== 'boolean' || typeof data.refresh_enabled !== 'boolean') return reply(ctx, 503, {error: 'Invalid bridge status'});
        return reply(ctx, 200, {pace_enabled: data.pace_enabled, refresh_enabled: data.refresh_enabled});
      } catch (_) { return reply(ctx, 503, {error: 'Bridge status unavailable'}); }
    }
  }, {
    scope: 'issue', method: 'GET', path: '/catalog',
    handle: function(ctx) {
      const issue = ctx.issue, user = ctx.currentUser;
      if (!user || user.login === 'guest' || user.isBanned) return reply(ctx, 401, {error: 'Sign-in required'});
      if (!issue || !issue.project || !['FILMPOC', 'FILMREAL'].includes(issue.project.key) || !issue.isReported || !issue.isVisibleTo(user)) {
        return reply(ctx, 404, {error: 'Film unavailable'});
      }
      const id = issue.fields['FilmIQ TMDB ID'], title = issue.summary;
      if (!Number.isSafeInteger(id) || id <= 0 || id > 2147483647 || typeof title !== 'string' || !title.trim() || title.length > 500) return reply(ctx, 400, {error: 'Film identity unavailable'});
      try {
        const connection = new http.Connection(URL);
        connection.bearerAuth(ctx.settings.bridgeToken);
        connection.addHeader('Content-Type', 'application/json');
        const response = connection.postSync('/catalog', null, JSON.stringify({tmdb_id: id, title}));
        if (response.code === 403) return reply(ctx, 403, {error: 'Film not approved'});
        if (response.code !== 200) return reply(ctx, 503, {error: 'Reviewed catalog unavailable'});
        const data = response.json();
        if (!data || !['unknown', 'available'].includes(data.status) || (data.status === 'available' && (!data.film || data.film.tmdb_id !== id))) return reply(ctx, 503, {error: 'Reviewed catalog unavailable'});
        return reply(ctx, 200, data);
      } catch (_) { return reply(ctx, 503, {error: 'Reviewed catalog unavailable'}); }
    }
  }],
  requirements: { filmId: { type: entities.Field.integerType, name: 'FilmIQ TMDB ID' } }
};
