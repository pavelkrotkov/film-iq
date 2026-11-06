import {hasStoredGenre} from "./stored_genres.js";
import {matchesFilmSearch} from "./film_search.js";
import {boundMovaryFilm} from "./movary_history.js";
import {reviewDirectorNames} from "./direct_reviews.js";
import {sourceYearLabel} from "./source_evidence.js";

// Pure extraction of YouTrack's existing client-side filtering logic.
export const field = (film, name) => film.customFields?.find((item) => item.name === name)?.value ?? null;

export function filmYearLabel(film, liveYear = null) {
  const labels = [];
  const release = field(film, "FilmIQ Release Year");
  const source = field(film, "FilmIQ Source Year");
  const valid = (year) => Number.isInteger(year) && year > 0 && year <= 9999;
  if (valid(release)) labels.push(`Stored release year ${release}`);
  const sourceLabel = valid(source) ? sourceYearLabel(field(film, "FilmIQ Source Evidence")?.text, field(film, "FilmIQ TMDB ID"), String(source)) : null;
  if (sourceLabel) labels.push(sourceLabel);
  if (!labels.length && valid(liveYear)) labels.push(`TMDB-supplied year ${liveYear}`);
  return labels.join(" · ") || "Year unknown";
}

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

export function localWatchlistLabel(preferences, issueId) {
  if (!preferences) return "Local watchlist unavailable";
  const value = preferences[issueId]?.watchlist;
  return value === true ? "On local watchlist" : value === false ? "Not on local watchlist" : "Local watchlist unknown";
}

export function providerObservation(film) {
  try {
    const live = film.live?.availability;
    if (live) {
      if (!["complete", "partial", "unknown"].includes(live.status) || !Array.isArray(live.offers) ||
          !live.offers.every((item) => item && typeof item.provider === "string" && item.provider.trim() && ["subscription", "rent", "buy", "free", "ads"].includes(item.kind))) return null;
      const providers = (kind) => [...new Set(live.offers.filter((item) => item.kind === kind).map((item) => item.provider))];
      return {source: "TMDB / JustWatch", status: live.status, subscription: providers("subscription"), rent: providers("rent"), buy: providers("buy"), free: providers("free"), ads: providers("ads"), checked_at: live.checked_at};
    }
    const raw = field(film, "FilmIQ Provider Observation");
    const value = JSON.parse(typeof raw === "string" ? raw : raw?.text || "null");
    if (!value || value.source !== "synthetic fixture, not TMDB") return null;
    const status = value.status || "complete";
    if (!["complete", "partial", "unknown"].includes(status)) return null;
    const list = (v) => Array.isArray(v) && v.every((item) => typeof item === "string" && item.trim()) ? v : null;
    const subscription = list(value.subscription), rent = list(value.rent);
    if (status === "complete" && (!subscription || !rent)) return null;
    return {source: "Synthetic fixture", status, subscription, rent, buy: list(value.buy), free: list(value.free), ads: list(value.ads), checked_at: typeof value.checked_at === "string" ? value.checked_at : null};
  } catch { return null; }
}

export function providerFreshness(observation, now = Date.now()) {
  if (!observation || observation.status === "unknown") return "unknown";
  const age = now - Date.parse(observation.checked_at || "");
  if (!Number.isFinite(age) || age < 0) return "unknown";
  return age <= 7 * 24 * 60 * 60 * 1000 ? "recent" : "stale";
}

export function filterYoutrackFilms(films, {preferences, query, stateFilter, minimum, watchlistOnly, sortInterest, movaryOnly, excludeMovaryWatched, movary, provider, genre, freshness, localWatched, showArchived, titleReviewOnly}) {
  const matching = films.filter((item) => {
    const personal = preferences?.[item.idReadable];
    if (!showArchived && stateFilter !== "Archived" && field(item, "FilmIQ Lifecycle")?.name === "Archived") return false;
    if (titleReviewOnly && !item.titleNeedsReview) return false;
    if (!matchesFilmSearch(query, item.summary, field(item, "FilmIQ Director"), item.live?.directors,
      query ? reviewDirectorNames(field(item, "FilmIQ Direct Review Links")?.text, field(item, "FilmIQ TMDB ID"), item.summary) : [])) return false;
    if (stateFilter && field(item, "FilmIQ Lifecycle")?.name !== stateFilter) return false;
    if (genre && !hasStoredGenre(field(item, "FilmIQ Genre"), genre) && !item.live?.genres?.includes(genre)) return false;
    if (provider || freshness) {
      const observation = providerObservation(item);
      if (provider && (observation?.status === "unknown" || !observation?.subscription?.includes(provider))) return false;
      if (freshness && providerFreshness(observation) !== freshness) return false;
    }
    if (minimum && (personal?.interest_score == null || personal.interest_score < Number(minimum))) return false;
    if (watchlistOnly && personal?.watchlist !== true) return false;
    if (localWatched && (!preferences || localWatchStatus(preferences, item.idReadable) !== localWatched)) return false;
    const watchedInMovary = boundMovaryFilm(movary, item.idReadable, field(item, "FilmIQ TMDB ID"));
    if (movaryOnly && !watchedInMovary) return false;
    if (excludeMovaryWatched && (movary?.status !== "available" || watchedInMovary)) return false;
    return true;
  });
  if (sortInterest) matching.sort((a, b) => (preferences?.[b.idReadable]?.interest_score ?? -1) - (preferences?.[a.idReadable]?.interest_score ?? -1));
  return matching;
}
