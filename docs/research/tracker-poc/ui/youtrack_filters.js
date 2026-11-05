// Pure extraction of YouTrack's existing client-side filtering logic.
export const field = (film, name) => film.customFields?.find((item) => item.name === name)?.value ?? null;

export function localWatchStatus(preferences, issueId) {
  if (!preferences || !Object.hasOwn(preferences, issueId)) return "unknown";
  const value = preferences[issueId]?.watched_at;
  if (value === null) return "not_recorded";
  return typeof value === "string" && value.trim() && Number.isFinite(Date.parse(value)) ? "watched" : "unknown";
}

export function localWatchLabel(preferences, issueId) {
  if (!preferences) return "Unavailable";
  const status = localWatchStatus(preferences, issueId);
  return status === "watched" ? "Watched timestamp recorded" : status === "not_recorded" ? "No watched timestamp recorded" : "Unknown";
}

export function providerObservation(film) {
  try {
    const live = film.live?.availability;
    if (live) {
      if (!["complete", "partial", "unknown"].includes(live.status) || !Array.isArray(live.offers) ||
          !live.offers.every((item) => item && typeof item.provider === "string" && item.provider.trim() && ["subscription", "rent", "buy", "free", "ads"].includes(item.kind))) return null;
      const providers = (kind) => [...new Set(live.offers.filter((item) => item.kind === kind).map((item) => item.provider))];
      return {source: "TMDB / JustWatch", status: live.status, subscription: providers("subscription"), rent: providers("rent"), checked_at: live.checked_at};
    }
    const raw = field(film, "FilmIQ Provider Observation");
    const value = JSON.parse(typeof raw === "string" ? raw : raw?.text || "null");
    if (!value || value.source !== "synthetic fixture, not TMDB") return null;
    const status = value.status || "complete";
    if (!["complete", "partial", "unknown"].includes(status)) return null;
    const list = (v) => Array.isArray(v) && v.every((item) => typeof item === "string" && item.trim()) ? v : null;
    const subscription = list(value.subscription), rent = list(value.rent);
    if (status === "complete" && (!subscription || !rent)) return null;
    return {source: "Synthetic fixture", status, subscription, rent, checked_at: typeof value.checked_at === "string" ? value.checked_at : null};
  } catch { return null; }
}

export function providerFreshness(observation, now = Date.now()) {
  if (!observation || observation.status === "unknown") return "unknown";
  const age = now - Date.parse(observation.checked_at || "");
  if (!Number.isFinite(age) || age < 0) return "unknown";
  return age <= 7 * 24 * 60 * 60 * 1000 ? "recent" : "stale";
}

export function filterYoutrackFilms(films, {preferences, query, stateFilter, minimum, watchlistOnly, sortInterest, movaryOnly, excludeMovaryWatched, movary, provider, genre, freshness, localWatched, showArchived}) {
  const matching = films.filter((item) => {
    const personal = preferences?.[item.idReadable];
    if (!showArchived && stateFilter !== "Archived" && field(item, "FilmIQ Lifecycle")?.name === "Archived") return false;
    if (query && !item.summary.toLowerCase().includes(query.toLowerCase())) return false;
    if (stateFilter && field(item, "FilmIQ Lifecycle")?.name !== stateFilter) return false;
    if (genre && field(item, "FilmIQ Genre") !== genre && !item.live?.genres?.includes(genre)) return false;
    if (provider || freshness) {
      const observation = providerObservation(item);
      if (provider && (observation?.status === "unknown" || !observation?.subscription?.includes(provider))) return false;
      if (freshness && providerFreshness(observation) !== freshness) return false;
    }
    if (minimum && (personal?.interest_score == null || personal.interest_score < Number(minimum))) return false;
    if (watchlistOnly && personal?.watchlist !== true) return false;
    if (localWatched && (!preferences || localWatchStatus(preferences, item.idReadable) !== localWatched)) return false;
    if (movaryOnly && (movary?.status !== "available" || movary?.films?.[item.idReadable]?.watched !== true)) return false;
    if (excludeMovaryWatched && (movary?.status !== "available" || movary?.films?.[item.idReadable]?.watched === true)) return false;
    return true;
  });
  if (sortInterest) matching.sort((a, b) => (preferences?.[b.idReadable]?.interest_score ?? -1) - (preferences?.[a.idReadable]?.interest_score ?? -1));
  return matching;
}
