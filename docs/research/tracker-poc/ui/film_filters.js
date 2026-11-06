import {hasStoredGenre} from "./stored_genres.js";
import {matchesFilmSearch} from "./film_search.js";
import {reviewDirectorNames} from "./direct_reviews.js";
import {sourceDirectorForSearch} from "./source_evidence.js";
import {tmdbId} from "./live_batch.js";

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
    const live = film.live?.availability;
    if (live) {
      if (!["complete", "partial"].includes(live.status)) return null;
      return [...new Set(live.offers.filter((offer) => offer.kind === "subscription").map((offer) => offer.provider))];
    }
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
  const availability = film.live?.availability;
  const checked = Date.parse(availability
    ? (["complete", "partial"].includes(availability.status) ? availability.checked_at : "")
    : syntheticAvailability(film)?.checked_at || "");
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
    movaryOnly,
    excludeMovaryWatched,
    showArchived,
    titleReviewOnly,
    movary,
  } = options;
  return films
    .filter(
      (item) =>
        (showArchived || lifecycle === "archived" || String(item.status).toLowerCase() !== "archived") &&
        (!titleReviewOnly || item.titleNeedsReview) &&
        matchesFilmSearch(query, item.title, query ? sourceDirectorForSearch(item.fields["POC Evidence"], tmdbId(item), item.fields["POC Source Director"]) : null, item.live?.directors,
          query ? reviewDirectorNames(item.fields["POC Direct Review Links"], item.fields["POC TMDB ID"], item.title) : []) &&
        (!provider || providers(item)?.includes(provider)) &&
        (!watchlistOnly || preferences?.[item.id]?.watchlist) &&
        (!movaryOnly || (movary?.status === "available" && movary?.films?.[item.fields["POC TMDB ID"]]?.watched === true)) &&
        (!excludeMovaryWatched || (movary?.status === "available" && movary?.films?.[item.fields["POC TMDB ID"]]?.watched !== true)) &&
        (!minimum ||
          (preferences?.[item.id]?.interest_score ?? 0) >= Number(minimum)) &&
        (!genre || hasStoredGenre(item.fields["POC Genre"], genre) || item.live?.genres?.includes(genre)) &&
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
