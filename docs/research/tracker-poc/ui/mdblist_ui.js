// Deliberately invoked by a user action; responses stay in page memory.
const DOMAINS = {
  tomatoes: "rottentomatoes.com", popcorn: "rottentomatoes.com",
  tomatoesaudience: "rottentomatoes.com", metacritic: "metacritic.com",
  metacriticuser: "metacritic.com", rogerebert: "rogerebert.com", imdb: "imdb.com",
  tmdb: "themoviedb.org", trakt: "trakt.tv", letterboxd: "letterboxd.com",
  myanimelist: "myanimelist.net",
};

export function safeSourceUrl(value, source) {
  const domain = DOMAINS[source];
  if (typeof value !== "string" || !domain) return null;
  try {
    const url = new URL(value);
    return url.protocol === "https:" && !url.username && !url.password &&
      (!url.port || url.port === "443") &&
      (url.hostname === domain || url.hostname.endsWith(`.${domain}`)) ? url.href : null;
  } catch {
    return null;
  }
}

export async function fetchRatings(tmdbId, fetcher = fetch) {
  if (!Number.isSafeInteger(tmdbId) || tmdbId <= 0 || tmdbId > 2147483647)
    throw new Error("MDBList lookup needs a valid TMDB ID.");
  let response;
  try {
    response = await fetcher(`http://localhost:15177/ratings/${tmdbId}`, {
      credentials: "include",
      cache: "no-store",
    });
  } catch {
    throw new Error("MDBList lookup unavailable; the local bridge may be offline.");
  }
  let payload;
  try {
    payload = await response.json();
  } catch {
    throw new Error("MDBList lookup unavailable; invalid response.");
  }
  if (!response.ok) {
    const message = payload?.error;
    if (typeof message === "string" &&
        (/^MDBList returned HTTP [1-5][0-9]{2}$/.test(message) ||
         ["MDBList rate limit reached; retry later", "MDBList key unavailable",
          "MDBList response identity did not match"].includes(message))) {
      throw new Error(message);
    }
    throw new Error("MDBList lookup unavailable; retry when ready.");
  }
  if (!payload || payload.tmdb_id !== tmdbId || !Array.isArray(payload.ratings))
    throw new Error("MDBList lookup unavailable; identity or response was invalid.");
  return payload.ratings.map((row) => ({
    source: typeof row?.source === "string" ? row.source : "unknown",
    source_name: typeof row?.source_name === "string" ? row.source_name : "Unknown source",
    kind: ["critic", "audience"].includes(row?.kind) ? row.kind : "unknown",
    score_100: typeof row?.score_100 === "number" && Number.isFinite(row.score_100) &&
      row.score_100 >= 0 && row.score_100 <= 100 ? row.score_100 : null,
    votes: Number.isSafeInteger(row?.votes) && row.votes >= 0 ? row.votes : null,
    url: safeSourceUrl(row?.url, row?.source),
  }));
}
