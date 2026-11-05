import { field } from "./youtrack_filters.js";
import { preserveEarlierPoster, runRemaining } from "./live_batch.js";

export class LiveRateLimited extends Error {}
export const LIVE_BATCH_LIMIT = 30;

export function suppliedTmdbId(film) {
  if (!film) return null;
  const id = field(film, "FilmIQ TMDB ID");
  return Number.isInteger(id) && id > 0 && id <= 2147483647 ? id : null;
}

export function sameNormalizedTitle(left, right) {
  if (typeof left !== "string" || typeof right !== "string") return false;
  const normalize = (value) => value.normalize("NFKC").toLowerCase().replace(/\s+/gu, " ").trim();
  const title = normalize(left);
  return Boolean(title) && title === normalize(right);
}

// An exact live title or original-title match is a display guard, not proof of identity.
export function matchesLiveTitle(title, data) {
  return typeof data?.title === "string" && !!data.title.trim() &&
    (sameNormalizedTitle(title, data.title) || sameNormalizedTitle(title, data.original_title));
}

export function liveMetadataMatches(film, data) {
  const id = suppliedTmdbId(film);
  return !!id && data?.tmdb_id === id && matchesLiveTitle(film?.summary, data);
}

export function attachMatchedLive(films, results) {
  return films.map((film) => {
    const data = results[film.idReadable]?.data;
    return liveMetadataMatches(film, data) ? {...film, live: data} : film;
  });
}

function safeUrl(value, host, path) {
  if (typeof value !== "string") return null;
  try {
    const url = new URL(value);
    return url.protocol === "https:" && url.hostname === host && !url.port && !url.username && !url.password && path(url) ? url.href : null;
  } catch { return null; }
}

export function safePosterUrl(value) {
  return safeUrl(value, "image.tmdb.org", (url) => /^\/t\/p\/w500\/[a-zA-Z0-9_.-]+$/.test(url.pathname) && !url.search && !url.hash);
}

function imdbUrl(value) {
  return safeUrl(value, "www.imdb.com", (url) => /^\/title\/tt[0-9]{7,15}\/$/.test(url.pathname) && !url.search && !url.hash);
}

function providerUrl(value) {
  return safeUrl(value, "www.themoviedb.org", () => true);
}

function strings(value) {
  return Array.isArray(value) && value.every((item) => typeof item === "string" && item.trim()) ? value : null;
}

function availability(value) {
  const unknown = {status: "unknown", checked_at: null, provider_url: null, offers: []};
  if (!value || !["complete", "partial", "unknown"].includes(value.status) ||
      !Array.isArray(value.offers) || !value.offers.every((offer) => offer &&
        typeof offer.provider === "string" && offer.provider.trim() &&
        ["subscription", "rent", "buy", "free", "ads"].includes(offer.kind))) return unknown;
  const checked = typeof value.checked_at === "string" && Number.isFinite(Date.parse(value.checked_at)) ? value.checked_at : null;
  return {status: value.status, checked_at: checked, provider_url: providerUrl(value.provider_url), offers: value.status === "unknown" ? [] : value.offers};
}

export function mergeLiveMetadata(previous, current) {
  const data = preserveEarlierPoster(previous, current);
  if (previous?.tmdb_id === data.tmdb_id && previous?.availability?.status === "complete" && data.availability.status !== "complete") {
    return {...data, availability: previous.availability, availability_attempt: data.availability.status};
  }
  return data;
}

export function mergeLiveResult(previous, outcome) {
  const oldId = previous?.requestedId ?? previous?.data?.tmdb_id;
  const requestedId = outcome.requestedId ?? outcome.data?.tmdb_id;
  const sameId = !oldId || !requestedId || oldId === requestedId;
  return outcome.data
    ? {data: mergeLiveMetadata(sameId ? previous?.data : null, outcome.data), error: null, requestedId}
    : {...(sameId ? previous : {}), ...outcome};
}

export function remainingLiveFilms(films, results) {
  return films.filter((film) => {
    const id = suppliedTmdbId(film), result = results[film.idReadable];
    return id && (!result || (result.requestedId ?? result.data?.tmdb_id) !== id);
  });
}

export function eligibleLiveFilms(films, results) {
  return remainingLiveFilms(films, results).slice(0, LIVE_BATCH_LIMIT);
}

export function failedLiveFilms(films, results) {
  return films.filter((film) => {
    const id = suppliedTmdbId(film), result = results[film.idReadable];
    return id && result?.error && (result.requestedId ?? result.data?.tmdb_id) === id;
  });
}

export async function runLiveBatch(host, films, active, onResult) {
  let succeeded = 0, failed = 0, rateLimited = false;
  for (const film of films.slice(0, LIVE_BATCH_LIMIT)) {
    if (!active()) break;
    try {
      const data = await readLiveMetadata(host, film);
      if (!active()) break;
      succeeded++;
      onResult(film, {data, requestedId: suppliedTmdbId(film)});
    } catch (error) {
      rateLimited = error instanceof LiveRateLimited;
      if (active()) {
        failed++;
        onResult(film, {requestedId: suppliedTmdbId(film), error: rateLimited ? "TMDB rate limit reached. Wait and reload the page before trying again." : "Live metadata is unavailable. No automatic retry was made."});
      }
      break; // The Host API does not guarantee an error shape, so unknown failures stop too.
    }
  }
  return {succeeded, failed, rateLimited, cancelled: !active()};
}

export function runRemainingLive(host, films, active, onResult) {
  return runRemaining(films, (chunk, report) => runLiveBatch(host, chunk, active, report), active, onResult);
}

export async function readLiveMetadata(host, film) {
  const id = suppliedTmdbId(film);
  if (!id || !/^(FILMPOC|FILMREAL)-[1-9]\d*$/.test(film?.idReadable || "")) throw new Error("Film identity unavailable");
  let result;
  try {
    result = await host.fetchYouTrack(`issues/${encodeURIComponent(film.idReadable)}/extensionEndpoints/filmiq-tmdb-live-isolated/metadata/read`, {method: "POST", body: {}});
  } catch (error) {
    if ([error?.status, error?.statusCode, error?.code, error?.response?.status].some((value) => Number(value) === 429) || /\b429\b/.test(error?.message || "")) throw new LiveRateLimited("TMDB rate limit reached");
    throw new Error("Live metadata unavailable");
  }
  if ([result?.status, result?.code].some((value) => Number(value) === 429)) throw new LiveRateLimited("TMDB rate limit reached");
  if (!result || result.tmdb_id !== id || typeof result.title !== "string" || !result.title.trim()) throw new Error("Metadata identity mismatch or invalid response");
  return {
    tmdb_id: id,
    title: result.title,
    original_title: typeof result.original_title === "string" && result.original_title.trim() ? result.original_title : null,
    synopsis: typeof result.synopsis === "string" && result.synopsis.trim() ? result.synopsis : null,
    year: Number.isInteger(result.year) && result.year > 0 && result.year <= 9999 ? result.year : null,
    genres: strings(result.genres),
    directors: strings(result.directors),
    poster_url: safePosterUrl(result.poster_url),
    imdb_title_url: imdbUrl(result.imdb_title_url),
    availability: availability(result.availability),
  };
}
