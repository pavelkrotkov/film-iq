// Freshness "unknown" asks for unknown data; the other filters exclude it.
export function filterMayExcludeUnknown({provider, genre, freshness}) {
  return Boolean(provider || genre || freshness === "recent" || freshness === "stale");
}
