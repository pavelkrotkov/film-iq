// Search only stored source assertions and already-matched live directors.
export function matchesFilmSearch(query, title, sourceDirector, liveDirectors, reviewDirectors = []) {
  if (!query) return true;
  const needle = query.toLowerCase();
  return [title, sourceDirector, ...(Array.isArray(liveDirectors) ? liveDirectors : []), ...reviewDirectors]
    .some((value) => typeof value === "string" && value.toLowerCase().includes(needle));
}
