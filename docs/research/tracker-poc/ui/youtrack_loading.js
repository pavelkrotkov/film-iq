// Read-only optional sources must not prevent canonical films from appearing.
export function publishFilmBatch(run, sequence, films, setFilms, setLoading) {
  if (run !== sequence.current) return;
  setFilms(films);
  setLoading(false);
}

export function boundedRead(operation, timeoutMs = 5000) {
  let timer;
  const timeout = new Promise((_, reject) => {
    timer = setTimeout(() => reject(new Error("Optional data request timed out")), timeoutMs);
  });
  return Promise.race([Promise.resolve().then(operation), timeout]).finally(() => clearTimeout(timer));
}

export async function loadFilmView({loadFilms, loadPreferences, loadWatched, publishFilms}, timeoutMs = 5000) {
  const films = await loadFilms();
  publishFilms(films);
  return Promise.allSettled([
    boundedRead(loadPreferences, timeoutMs),
    boundedRead(loadWatched, timeoutMs),
  ]);
}
