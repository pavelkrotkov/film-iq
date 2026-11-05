export function unavailableFilterSources({preferences, movary, minimum, watched, watchlistOnly, sortInterest, movaryOnly}) {
  const unavailable = [];
  if (!preferences && (minimum || watched || watchlistOnly || sortInterest)) unavailable.push("personal preferences");
  if (movary?.status !== "available" && movaryOnly) unavailable.push("Movary watched data");
  return unavailable;
}

export function missingLinkedFilm(selected, film, loaded, busy) {
  return Boolean(selected && !film && loaded && !busy);
}
