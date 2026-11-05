export function safeReviewUrl(value) {
  try {
    const url = new URL(value);
    return ["http:", "https:"].includes(url.protocol) && !url.username && !url.password ? url.href : null;
  } catch { return null; }
}

function validEvidence(evidence) {
  return !!evidence && typeof evidence.input_title === "string" && typeof evidence.source_page_title === "string" && Array.isArray(evidence.source_directors) && evidence.source_directors.length > 0 && evidence.source_directors.every((item) => typeof item === "string" && item.length > 0) && (evidence.source_year === null || Number.isInteger(evidence.source_year)) && Array.isArray(evidence.corroboration_urls) && evidence.corroboration_urls.length === 0 && evidence.identity_caveat === "Source-supplied film identity not independently verified." && evidence.details_note === "Additional identity details are retained privately.";
}

export function readDirectReviews(raw, filmId) {
  try {
    const value = JSON.parse(raw);
    if (value?.schema_version !== 1 || !Number.isSafeInteger(value.tmdb_id) || value.tmdb_id <= 0 || String(value.tmdb_id) !== String(filmId) || !Array.isArray(value.links)) return null;
    if (!value.links.every((link) => safeReviewUrl(link.url) && typeof link.provider === "string" && ["individual_critic_review", "review_aggregator_title_page"].includes(link.type) && typeof link.checked_at === "string" && validEvidence(link.identity_evidence))) return null;
    return value.links;
  } catch { return null; }
}

export function reviewsMatchTitle(links, title) {
  return Array.isArray(links) && typeof title === "string" && links.every((link) => link.identity_evidence.input_title === title);
}
