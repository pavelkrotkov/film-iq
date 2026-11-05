// Preserve the two Movary observations separately; an absent film is unknown.
function validDate(value) {
  if (value === null) return true;
  if (typeof value !== "string" || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;
  const date = new Date(`${value}T00:00:00.000Z`);
  return Number.isFinite(date.getTime()) && date.toISOString().slice(0, 10) === value;
}

export function movaryHistory(snapshot, issueId) {
  const film = snapshot?.status === "available" && snapshot.films?.[issueId];
  if (!film || film.watched !== true) return null;
  const plays = film.played_watch_dates;
  const exports = film.history_export_dates;
  return {
    observedAt: typeof snapshot.observed_at === "string" ? snapshot.observed_at : null,
    plays: Array.isArray(plays) && plays.every((event) => event && validDate(event.date) && Number.isSafeInteger(event.plays) && event.plays > 0) ? plays : null,
    exportDates: Array.isArray(exports) && exports.every(validDate) ? exports : null,
  };
}
