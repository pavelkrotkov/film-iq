export function syntheticAvailability(film) {
  try {
    const value = JSON.parse(
      film.fields["POC Synthetic Availability"] || "null",
    );
    if (!value || value.source !== "synthetic fixture, not TMDB") return null;
    if (!Array.isArray(value.subscription) || !Array.isArray(value.rent))
      return null;
    return value;
  } catch {
    return null;
  }
}

export function providers(film) {
  try {
    const observation = syntheticAvailability(film);
    if (observation) return observation.subscription;
    const raw =
      film.fields["POC Subscription Providers"] || film.fields["POC Streaming"];
    if (!raw) return null;
    const value = JSON.parse(raw);
    return Array.isArray(value) ? value : null;
  } catch {
    return null;
  }
}

export function freshness(film, now = Date.now()) {
  const checked = Date.parse(syntheticAvailability(film)?.checked_at || "");
  const age = now - checked;
  if (!Number.isFinite(age) || age < 0) return "unknown";
  return age <= 7 * 24 * 60 * 60 * 1000 ? "recent" : "stale";
}

export function filterFilms(films, options) {
  const {
    query,
    provider,
    watchlistOnly,
    minimum,
    genre,
    lifecycle,
    watched,
    freshnessFilter,
    sortInterest,
    preferences,
  } = options;
  return films
    .filter(
      (item) =>
        item.title.toLowerCase().includes(query.toLowerCase()) &&
        (!provider || providers(item)?.includes(provider)) &&
        (!watchlistOnly || preferences?.[item.id]?.watchlist) &&
        (!minimum ||
          (preferences?.[item.id]?.interest_score ?? 0) >= Number(minimum)) &&
        (!genre || item.fields["POC Genre"] === genre) &&
        (!lifecycle || item.status === lifecycle) &&
        (!watched ||
          (preferences?.[item.id] &&
            (watched === "marked") ===
              Boolean(preferences[item.id]?.watched_at))) &&
        (!freshnessFilter || freshness(item) === freshnessFilter),
    )
    .sort((a, b) =>
      sortInterest
        ? (preferences?.[b.id]?.interest_score ?? -1) -
          (preferences?.[a.id]?.interest_score ?? -1)
        : 0,
    );
}
