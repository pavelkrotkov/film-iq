// User-initiated, page-memory-only reads. One film may require three TMDB calls.
export const BATCH_LIMIT = 30;

export class RateLimitError extends Error {}
export class AccessDeniedError extends Error {}
export const ACCESS_DENIED_MESSAGE = "Metadata access was denied. Check your sign-in, the film's lookup authorization and the provider credential before retrying.";

export function accessDenied(value) {
  return [value?.status, value?.statusCode, value?.code, value?.response?.status].some((status) => status === 401 || status === 403 || status === "401" || status === "403") ||
    (typeof value?.message === "string" && /\b(?:HTTP\s+40[13]|401\s+Unauthorized|403\s+Forbidden)\b/i.test(value.message));
}

export function safeImdbTitleUrl(value) {
  return typeof value === "string" && /^https:\/\/www\.imdb\.com\/title\/tt[0-9]{7,15}\/$/.test(value) ? value : null;
}

export async function fetchLiveMovie(id, signal, fetcher = fetch) {
  const response = await fetcher(`http://localhost:15176/movie/${id}`, {
    cache: "no-store", credentials: "include", signal,
  });
  if (response.status === 429) throw new RateLimitError();
  if (accessDenied(response)) throw new AccessDeniedError();
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
  if (accessDenied(response)) throw new AccessDeniedError();
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
  if (accessDenied(response)) throw new AccessDeniedError();
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

// A cache-only read may update an unchanged result, but must not overwrite an
// explicit refresh or failure that finished while the cache read was pending.
export function hydrateCachedResult(previous, key, id, data, expected) {
  if (!Number.isInteger(id) || id <= 0 || data?.tmdb_id !== id) return previous;
  const current = previous[key];
  if (current !== expected) return previous;
  const currentId = current?.requestedId ?? current?.data?.tmdb_id;
  const sameId = currentId === id;
  // Cache-only responses do not include the latest interactive-attempt flags.
  // Keep those warnings, and any failure, until another explicit attempt.
  const notices = sameId ? {
    ...(current?.data?.metadata_attempt === 'incomplete' ? {metadata_attempt:'incomplete'} : {}),
    ...(['partial','unknown'].includes(current?.data?.availability_attempt)
      ? {availability_attempt:current.data.availability_attempt} : {}),
  } : {};
  const hydrated = Object.keys(notices).length ? {...data, ...notices} : data;
  return {...previous, [key]: {...(sameId && current?.error ? {error:current.error} : {}), data:hydrated, requestedId:id}};
}

export function tmdbId(film) {
  const value = film.fields["POC TMDB ID"];
  return typeof value === "string" && /^[1-9][0-9]{0,9}$/.test(value) &&
    Number(value) <= 2147483647 ? Number(value) : null;
}

export function availabilityTimeLabel(status, checkedAt) {
  if (!checkedAt) return status === "unknown" ? "Attempt time unknown" : "Check time unknown";
  return `${status === "unknown" ? "Attempted" : "Checked"}: ${checkedAt}`;
}

// Only report on the current ID; displayed is already gated by the title match.
export function refreshNotice(result, expectedId, displayed) {
  if (!expectedId || (result?.requestedId ?? result?.data?.tmdb_id) !== expectedId) return null;
  const previousShown = !!displayed && displayed === result?.data;
  if (result?.error) return previousShown ? "Your last in-app refresh failed; available data shown." : "Your last in-app refresh failed.";
  if (previousShown && displayed.metadata_attempt && displayed.availability_attempt) return "Your last in-app metadata and provider check was incomplete; shown data may come from another check.";
  if (previousShown && displayed.metadata_attempt) return "Your last in-app metadata check was incomplete; shown details may come from another check.";
  if (previousShown && displayed.availability_attempt) return "Your last in-app provider check was incomplete; shown availability may come from another check.";
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
  let succeeded = 0, failed = 0, rateLimited = false, denied = false;
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
      denied = error instanceof AccessDeniedError;
      onResult(film.id, { requestedId, error: rateLimited ? "TMDB rate limit reached; wait before retrying." : denied ? ACCESS_DENIED_MESSAGE : "Live metadata unavailable; retry when ready." }, succeeded + failed);
      if (rateLimited || denied || stopOnError) break;
    }
  }
  return { succeeded, failed, cancelled: signal.aborted, rateLimited, ...(denied ? {accessDenied:true} : {}) };
}

// Each chunk uses the existing 30-film runner; callers must invoke this explicitly.
export async function runRemaining(films, runChunk, active, onResult) {
  let succeeded = 0, failed = 0, rateLimited = false, denied = false, done = 0;
  for (let start = 0; start < films.length && active(); start += BATCH_LIMIT) {
    const result = await runChunk(films.slice(start, start + BATCH_LIMIT), (...args) => {
      if (active()) onResult(...args, ++done, films.length);
    });
    succeeded += result.succeeded;
    failed += result.failed;
    rateLimited ||= result.rateLimited;
    denied ||= !!result.accessDenied;
    if (result.failed || result.cancelled || !active()) break;
  }
  return {succeeded, failed, rateLimited, cancelled: !active(), ...(denied ? {accessDenied:true} : {})};
}

export function runRemainingBatch(films, fetchMovie, signal, onResult) {
  return runRemaining(films, (chunk, report) => runBatch(chunk, fetchMovie, signal,
    (id, result) => report(id, result), {stopOnError: true}), () => !signal.aborted, onResult);
}
