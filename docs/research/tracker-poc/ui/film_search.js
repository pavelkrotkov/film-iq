// Only search source-listed and already-matched live directors; absent data is unknown.
export function matchesFilmSearch(query, title, sourceDirector, liveDirectors) {
  if (!query) return true;
  const needle = query.toLowerCase();
  return [title, sourceDirector, ...(Array.isArray(liveDirectors) ? liveDirectors : [])]
    .some((value) => typeof value === "string" && value.toLowerCase().includes(needle));
}
