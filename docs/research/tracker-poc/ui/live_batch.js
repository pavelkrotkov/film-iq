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

export function tmdbId(film) {
  const value = film.fields["POC TMDB ID"];
  return typeof value === "string" && /^[1-9][0-9]{0,9}$/.test(value) &&
    Number(value) <= 2147483647 ? Number(value) : null;
}

export function chooseBatch(films, results, retry = false) {
  return films
    .filter((film) => {
      const id = tmdbId(film), result = results[film.id];
      const current = result && (result.requestedId ?? result.data?.tmdb_id) === id;
      return id && (retry ? current && result.error : !current);
    })
    .slice(0, BATCH_LIMIT);
}

export function mergeResult(previous, result) {
  if (!result.data) return { ...previous, ...result };
  const previousAvailability = previous?.data?.availability;
  const currentAvailability = result.data.availability;
  if (previous?.data?.tmdb_id === result.data.tmdb_id && previousAvailability?.status === "complete" && currentAvailability?.status !== "complete") {
    return { ...result, data: { ...result.data, availability: previousAvailability,
      availability_attempt: currentAvailability?.status || "unknown" } };
  }
  return result;
}

export async function runBatch(films, fetchMovie, signal, onResult) {
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
      if (rateLimited) break;
    }
  }
  return { succeeded, failed, cancelled: signal.aborted, rateLimited };
}
