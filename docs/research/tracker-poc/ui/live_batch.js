// User-initiated, page-memory-only reads. One film may require three TMDB calls.
export const BATCH_LIMIT = 30;

export class RateLimitError extends Error {}

export function safeImdbTitleUrl(value) {
  return typeof value === "string" && /^https:\/\/www\.imdb\.com\/title\/tt[0-9]{7,15}\/$/.test(value) ? value : null;
}

export async function fetchLiveMovie(id, signal, fetcher = fetch) {
  const response = await fetcher(`http://localhost:15176/movie/${id}`, {
    cache: "no-store", credentials: "include", signal,
  });
  if (response.status === 429) throw new RateLimitError();
  if (!response.ok) throw new Error("Live metadata unavailable");
  const data = await response.json();
  if (!data.availability || !Array.isArray(data.availability.offers)) throw new Error("Invalid metadata response");
  return data;
}

// The cache-only path never initiates a provider request.
export async function fetchCachedMovie(film, signal, fetcher = fetch) {
  const id = tmdbId(film);
  if (!id || !/^[A-Za-z0-9_-]{1,200}$/.test(film.id || "")) throw new Error("Film identity unavailable");
  const response = await fetcher(`http://localhost:15176/cache/${encodeURIComponent(film.id)}`, {
    cache: "no-store", credentials: "include", signal,
  });
  if (!response.ok) throw new Error("Cached metadata unavailable");
  const data = await response.json();
  if (data.tmdb_id !== id || !data.availability || !Array.isArray(data.availability.offers) || !Number.isFinite(Date.parse(data.cache_expires_at)) || Date.parse(data.cache_expires_at) <= Date.now()) throw new Error("Invalid or expired cached metadata");
  return data;
}

export async function fetchTaskLiveMovie(film, signal, fetcher = fetch) {
  const id = tmdbId(film);
  if (!id || !/^[A-Za-z0-9_-]{1,200}$/.test(film.id || "")) throw new Error("Film identity unavailable");
  const response = await fetcher(`http://localhost:15176/refresh/${encodeURIComponent(film.id)}`, {
    cache: "no-store", credentials: "include", signal,
  });
  if (response.status === 429) throw new RateLimitError();
  if (!response.ok) throw new Error("Live metadata unavailable");
  const data = await response.json();
  if (data.tmdb_id !== id || !data.availability || !Array.isArray(data.availability.offers) || !Number.isFinite(Date.parse(data.cache_expires_at)) || Date.parse(data.cache_expires_at) <= Date.now()) throw new Error("Invalid or expired metadata response");
  return data;
}

export function expireCachedResults(results, now = Date.now()) {
  let changed = false, next = Infinity;
  const remaining = {};
  for (const [key, value] of Object.entries(results)) {
    const expiry = value?.data?.cache_expires_at;
    if (expiry) {
      const timestamp = Date.parse(expiry);
      if (!Number.isFinite(timestamp) || timestamp <= now) { changed = true; continue; }
      next = Math.min(next, timestamp);
    }
    remaining[key] = value;
  }
  return {results: changed ? remaining : results, next};
}

export function tmdbId(film) {
  const value = film.fields["POC TMDB ID"];
  return typeof value === "string" && /^[1-9][0-9]{0,9}$/.test(value) &&
    Number(value) <= 2147483647 ? Number(value) : null;
}

// Only report on the current ID; displayed is already gated by the title match.
export function refreshNotice(result, expectedId, displayed) {
  if (!expectedId || (result?.requestedId ?? result?.data?.tmdb_id) !== expectedId) return null;
  const previousShown = !!displayed && displayed === result?.data;
  if (result?.error) return previousShown ? "Latest refresh failed; previous data shown." : "Latest refresh failed.";
  if (previousShown && displayed.availability_attempt) return "Latest provider check incomplete; previous availability shown.";
  return null;
}

export function chooseRemaining(films, results, retry = false) {
  return films
    .filter((film) => {
      const id = tmdbId(film), result = results[film.id];
      const current = result && (result.requestedId ?? result.data?.tmdb_id) === id;
      return id && (retry ? current && result.error : !current);
    });
}

export function chooseBatch(films, results, retry = false) {
  return chooseRemaining(films, results, retry).slice(0, BATCH_LIMIT);
}

// A missing poster is unknown; retain one from the same ID and unchanged title.
export function carryIsFresh(previous, now = Date.now()) {
  if (!previous || previous.cache_expires_at == null) return true;
  const deadline = Date.parse(previous.cache_expires_at);
  return Number.isFinite(deadline) && deadline > now;
}

export function carryEarlierDeadline(previous, current) {
  const oldDeadline = Date.parse(previous?.cache_expires_at);
  const newDeadline = Date.parse(current?.cache_expires_at);
  return Number.isFinite(oldDeadline) && (!Number.isFinite(newDeadline) || oldDeadline < newDeadline)
    ? {...current, cache_expires_at: previous.cache_expires_at} : current;
}

export function preserveEarlierPoster(previous, current) {
  if (previous?.tmdb_id && previous.tmdb_id === current?.tmdb_id &&
      carryIsFresh(previous) &&
      typeof previous.title === "string" && !!previous.title.trim() && previous.title === current.title &&
      typeof previous.poster_url === "string" && !!previous.poster_url && current.poster_url == null) {
    return carryEarlierDeadline(previous, {...current, poster_url: previous.poster_url, poster_from_previous: true});
  }
  return current;
}

export function mergeResult(previous, result) {
  if (!result.data) {
    const oldId = previous?.requestedId ?? previous?.data?.tmdb_id;
    return { ...(oldId && result.requestedId && oldId !== result.requestedId || !carryIsFresh(previous?.data) ? {} : previous), ...result };
  }
  const data = preserveEarlierPoster(previous?.data, result.data);
  const previousAvailability = previous?.data?.availability;
  const currentAvailability = data.availability;
  if (previous?.data?.tmdb_id === data.tmdb_id && carryIsFresh(previous?.data) && previousAvailability?.status === "complete" && currentAvailability?.status !== "complete") {
    return { ...result, data: carryEarlierDeadline(previous.data, { ...data, availability: previousAvailability,
      availability_attempt: currentAvailability?.status || "unknown" }) };
  }
  return data === result.data ? result : {...result, data};
}

export async function runBatch(films, fetchMovie, signal, onResult, {stopOnError = false} = {}) {
  let succeeded = 0, failed = 0, rateLimited = false;
  for (const film of films.slice(0, BATCH_LIMIT)) {
    if (signal.aborted) break;
    const requestedId = tmdbId(film);
    try {
      const data = await fetchMovie(requestedId, signal);
      if (signal.aborted) break;
      if (data.tmdb_id !== requestedId) throw new Error("TMDB identity mismatch");
      succeeded++;
      onResult(film.id, { data, error: null, requestedId }, succeeded + failed);
    } catch (error) {
      if (signal.aborted) break;
      failed++;
      rateLimited = error instanceof RateLimitError;
      onResult(film.id, { requestedId, error: rateLimited ? "TMDB rate limit reached; wait before retrying." : "Live metadata unavailable; retry when ready." }, succeeded + failed);
      if (rateLimited || stopOnError) break;
    }
  }
  return { succeeded, failed, cancelled: signal.aborted, rateLimited };
}

// Each chunk uses the existing 30-film runner; callers must invoke this explicitly.
export async function runRemaining(films, runChunk, active, onResult) {
  let succeeded = 0, failed = 0, rateLimited = false, done = 0;
  for (let start = 0; start < films.length && active(); start += BATCH_LIMIT) {
    const result = await runChunk(films.slice(start, start + BATCH_LIMIT), (...args) => {
      if (active()) onResult(...args, ++done, films.length);
    });
    succeeded += result.succeeded;
    failed += result.failed;
    rateLimited ||= result.rateLimited;
    if (result.failed || result.cancelled || !active()) break;
  }
  return {succeeded, failed, rateLimited, cancelled: !active()};
}

export function runRemainingBatch(films, fetchMovie, signal, onResult) {
  return runRemaining(films, (chunk, report) => runBatch(chunk, fetchMovie, signal,
    (id, result) => report(id, result), {stopOnError: true}), () => !signal.aborted, onResult);
}
