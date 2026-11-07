import {sameNormalizedTitle} from "./youtrack_tmdb.js";

// Do not display an expired, mismatched or malformed catalog response.
export function reviewedCatalog(value, tmdbId, trackerTitle, now = Date.now()) {
  const text = (item, limit) => typeof item === "string" && !!item.trim() && item.length <= limit;
  const timestamp = (item) => {
    if (typeof item !== "string" || !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-]\d{2}:\d{2})$/.test(item)) return NaN;
    const day = new Date(`${item.slice(0, 10)}T00:00:00.000Z`);
    return Number.isFinite(day.getTime()) && day.toISOString().slice(0, 10) === item.slice(0, 10) ? Date.parse(item) : NaN;
  };
  if (!value || !Number.isInteger(tmdbId) || tmdbId <= 0 || value.tmdb_id !== tmdbId ||
      !text(value.title, 512) || !text(value.original_title, 512) ||
      !(sameNormalizedTitle(trackerTitle, value.title) || sameNormalizedTitle(trackerTitle, value.original_title)) ||
      !Array.isArray(value.directors) || !value.directors.length || value.directors.length > 20 ||
      !value.directors.every((item) => text(item, 256)) ||
      !(value.year === null || (Number.isInteger(value.year) && value.year > 0 && value.year <= 9999)) ||
      !(value.runtime_minutes === null || (Number.isInteger(value.runtime_minutes) && value.runtime_minutes > 0 && value.runtime_minutes <= 10000)) ||
      value.source !== "Reviewed display catalog" || !text(value.attribution, 1000) ||
      typeof value.observed_at !== "string" || typeof value.expires_at !== "string") return null;
  const observed = timestamp(value.observed_at), expires = timestamp(value.expires_at);
  if (!Number.isFinite(observed) || !Number.isFinite(expires) || observed > now || expires <= now || expires <= observed || expires - observed > 180 * 86400000) return null;
  return value;
}

export async function readReviewedCatalog(source, filmId, host, fetcher = fetch) {
  if (typeof filmId !== "string" || !filmId) return null;
  if (source === "kaneo") {
    const response = await fetcher(`http://localhost:15176/catalog/${encodeURIComponent(filmId)}`, {credentials: "include", cache: "no-store"});
    return response.ok ? response.json() : null;
  }
  if (source === "youtrack") {
    const result = await host.fetchYouTrack(`issues/${encodeURIComponent(filmId)}/extensionEndpoints/filmiq-tmdb-live-isolated/metadata/catalog`, {method: "GET"});
    return result?.status === "available" ? result.film : null;
  }
  return null;
}
