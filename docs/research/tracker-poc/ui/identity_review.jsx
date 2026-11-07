import React from "react";
import { readDirectReviews, reviewsMatchTitle, safeReviewUrl } from "./direct_reviews.js";
import { safeImdbTitleUrl } from "./live_batch.js";
import { sameNormalizedTitle, titleNeedsReview } from "./youtrack_tmdb.js";

const text = (value) => typeof value === "string" && value.trim() ? value.trim() : "Unknown";
const year = (value) => {
  const parsed = typeof value === "string" && /^[0-9]{1,4}$/.test(value) ? Number(value) : value;
  return Number.isInteger(parsed) && parsed > 0 && parsed <= 9999 ? String(parsed) : "Unknown";
};

// Show only facts from the currently supplied ID; this is not a match decision.
export function IdentityReview({ expectedId, savedTitle, sourceYear, sourceDirector, reviewEvidence, data, provider = "TMDB" }) {
  if (!titleNeedsReview(expectedId, savedTitle, data)) return null;
  const directors = Array.isArray(data.directors) && data.directors.length && data.directors.every((item) => typeof item === "string" && item.trim())
    ? data.directors.map((item) => item.trim()).join(", ") : "Unknown";
  const candidate = provider === "TMDB" ? safeImdbTitleUrl(data.imdb_title_url) : null;
  const reviews = provider === "TMDB" ? readDirectReviews(reviewEvidence, expectedId) : null;
  const matchingReviews = reviewsMatchTitle(reviews, savedTitle) ? reviews.filter(({identity_evidence: evidence}) =>
    sameNormalizedTitle(evidence.source_page_title, data.title) || sameNormalizedTitle(evidence.source_page_title, data.original_title)
  ) : [];
  return <section role="alert">
    <h4>Film identity needs review</h4>
    <p>The saved title does not match the provider title. These may be different films or alternate titles. Compare the source evidence before using this metadata. Artwork and streaming offers are withheld.</p>
    <p><strong>Saved record</strong><br />Title: {text(savedTitle)}<br />Source-listed year: {year(sourceYear)}<br />Source-listed director: {text(sourceDirector)}</p>
    <p><strong>{provider} response</strong><br />Title: {text(data.title)}<br />Original title: {text(data.original_title)}<br />Release year: {year(data.year)}<br />Director: {directors}</p>
    {matchingReviews.length > 0 && <div><p>Existing review evidence uses a matching provider title. This is an unverified identity lead, not a confirmed film match.</p><ul>{matchingReviews.map((review) => <li key={review.url}><a href={safeReviewUrl(review.url)} target="_blank" rel="noreferrer">{review.provider}: {review.identity_evidence.source_page_title} ↗</a></li>)}</ul></div>}
    {candidate && <p><a href={candidate} target="_blank" rel="noreferrer">Open candidate IMDb title page ↗</a>. IMDb ID supplied by TMDB; the film match is not independently verified. Opening the link visits IMDb.</p>}
    <p>These values do not confirm a match. A source-listed year may differ from the release year.</p>
  </section>;
}
