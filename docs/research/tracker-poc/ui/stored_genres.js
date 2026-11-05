// Both trackers currently store genres in a text field. Only the prefixed
// representation is interpreted as structured data; old text stays one label.
export const GENRES_PREFIX = "filmiq-genres-v1:";

const validGenres = (value) => Array.isArray(value) && value.every(
  (genre) => typeof genre === "string" && !!genre.trim() && !/[\r\n]/.test(genre),
);

export function decodeStoredGenres(raw) {
  if (raw == null || raw === "") return {status: "unknown", genres: []};
  if (typeof raw !== "string") return {status: "invalid", genres: []};
  if (!raw.startsWith(GENRES_PREFIX)) {
    return validGenres([raw]) ? {status: "known", genres: [raw]} : {status: "invalid", genres: []};
  }
  try {
    const genres = JSON.parse(raw.slice(GENRES_PREFIX.length));
    return validGenres(genres) ? {status: "known", genres} : {status: "invalid", genres: []};
  } catch {
    return {status: "invalid", genres: []};
  }
}

// A known-empty array is representable. Editor clear actions continue to map
// to each tracker's existing unknown value (null or empty string).
export function encodeStoredGenres(genres) {
  if (!validGenres(genres)) throw new Error("Genres must be nonempty text labels.");
  return GENRES_PREFIX + JSON.stringify(genres);
}

export function hasStoredGenre(raw, genre) {
  const decoded = decodeStoredGenres(raw);
  return decoded.status === "known" && decoded.genres.includes(genre);
}

export function storedGenreLabels(raw) {
  const decoded = decodeStoredGenres(raw);
  return decoded.status === "known" ? decoded.genres : [];
}

export function storedGenreText(raw) {
  return storedGenreLabels(raw).join("\n");
}

export function storedGenreDisplay(raw) {
  const decoded = decodeStoredGenres(raw);
  if (decoded.status === "unknown") return null;
  if (decoded.status === "invalid") return "Stored genres invalid";
  return decoded.genres.length ? decoded.genres.join(", ") : "No stored genres";
}

// Do not rewrite legacy scalar values, even when another field is saved.
export function genreEdit(raw, text, clearValue, resetKnownEmpty = false) {
  const decoded = decodeStoredGenres(raw);
  if (decoded.status === "invalid" || typeof text !== "string") throw new Error("Stored genres are invalid; copy the draft before reloading.");
  if (resetKnownEmpty && text === "" && decoded.status === "known" && !decoded.genres.length) return {changed: true, value: clearValue};
  if (text === storedGenreText(raw)) return {changed: false, value: raw};
  if (text === "") return {changed: true, value: clearValue};
  const genres = text.split("\n");
  if (!validGenres(genres)) throw new Error("Enter one nonblank genre per line, or clear the field.");
  return {changed: true, value: encodeStoredGenres(genres)};
}
