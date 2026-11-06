// Preserve the two Movary observations separately; an absent film is unknown.
export const MOVARY_MAPPING_NOTICE = "Shown watched entries are associated using supplied TMDB IDs and may be inferred from matching source events. Film identity has not been independently verified.";

function validDate(value) {
  if (value === null) return true;
  if (typeof value !== "string" || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;
  const date = new Date(`${value}T00:00:00.000Z`);
  return Number.isFinite(date.getTime()) && date.toISOString().slice(0, 10) === value;
}

export function boundMovaryFilm(snapshot, issueId, tmdbId) {
  const film = snapshot?.status === "available" && snapshot.films?.[issueId];
  return film && film.watched === true && Number.isSafeInteger(tmdbId) && tmdbId > 0 && film.tmdb_id === tmdbId ? film : null;
}

function history(snapshot, film) {
  if (!film) return null;
  const plays = film.played_watch_dates;
  const exports = film.history_export_dates;
  return {
    observedAt: typeof snapshot.observed_at === "string" ? snapshot.observed_at : null,
    plays: Array.isArray(plays) && plays.every((event) => event && validDate(event.date) && Number.isSafeInteger(event.plays) && event.plays > 0) ? plays : null,
    exportDates: Array.isArray(exports) && exports.every(validDate) ? exports : null,
  };
}

export function movaryHistory(snapshot, issueId, tmdbId) {
  return history(snapshot, boundMovaryFilm(snapshot, issueId, tmdbId));
}

// Only v2's explicitly unbound entry is available as issue-scoped evidence.
export function unboundMovaryHistory(snapshot, issueId) {
  const film = snapshot?.status === "available" && snapshot.films?.[issueId];
  return history(snapshot, film?.watched === true && film.tmdb_id === null ? film : null);
}
