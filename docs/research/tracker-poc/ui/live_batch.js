// User-initiated, page-memory-only reads. One film may require three TMDB calls.
export const BATCH_LIMIT = 30;

export function tmdbId(film) {
  const value = film.fields["POC TMDB ID"];
  return typeof value === "string" && /^[1-9][0-9]{0,9}$/.test(value) &&
    Number(value) <= 2147483647 ? Number(value) : null;
}

export function chooseBatch(films, results, retry = false) {
  return films
    .filter((film) => tmdbId(film) && (retry ? results[film.id]?.error : !results[film.id]))
    .slice(0, BATCH_LIMIT);
}

export function mergeResult(previous, result) {
  if (!result.data) return { ...previous, ...result };
  const previousAvailability = previous?.data?.availability;
  const currentAvailability = result.data.availability;
  if (previousAvailability?.status === "complete" && currentAvailability?.status !== "complete") {
    return { ...result, data: { ...result.data, availability: previousAvailability,
      availability_attempt: currentAvailability?.status || "unknown" } };
  }
  return result;
}

export async function runBatch(films, fetchMovie, signal, onResult) {
  let succeeded = 0, failed = 0;
  for (const film of films.slice(0, BATCH_LIMIT)) {
    if (signal.aborted) break;
    try {
      const data = await fetchMovie(tmdbId(film), signal);
      if (signal.aborted) break;
      if (data.tmdb_id !== tmdbId(film)) throw new Error("TMDB identity mismatch");
      succeeded++;
      onResult(film.id, { data, error: null }, succeeded + failed);
    } catch {
      if (signal.aborted) break;
      failed++;
      onResult(film.id, { error: "Live metadata unavailable; retry when ready." }, succeeded + failed);
    }
  }
  return { succeeded, failed, cancelled: signal.aborted };
}
