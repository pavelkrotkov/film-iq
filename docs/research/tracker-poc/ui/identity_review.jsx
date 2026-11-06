import React from "react";
import { matchesLiveTitle } from "./youtrack_tmdb.js";

const text = (value) => typeof value === "string" && value.trim() ? value.trim() : "Unknown";
const year = (value) => {
  const parsed = typeof value === "string" && /^[0-9]{1,4}$/.test(value) ? Number(value) : value;
  return Number.isInteger(parsed) && parsed > 0 && parsed <= 9999 ? String(parsed) : "Unknown";
};

// Show only facts from the currently supplied ID; this is not a match decision.
export function IdentityReview({ expectedId, savedTitle, sourceYear, sourceDirector, data, provider = "TMDB" }) {
  if (!Number.isInteger(expectedId) || expectedId <= 0 || data?.tmdb_id !== expectedId || matchesLiveTitle(savedTitle, data)) return null;
  const directors = Array.isArray(data.directors) && data.directors.length && data.directors.every((item) => typeof item === "string" && item.trim())
    ? data.directors.map((item) => item.trim()).join(", ") : "Unknown";
  return <section role="alert">
    <h4>Film identity needs review</h4>
    <p>The saved title does not match the provider title. These may be different films or alternate titles. Compare the source evidence before using this metadata. Artwork and streaming offers are withheld.</p>
    <p><strong>Saved record</strong><br />Title: {text(savedTitle)}<br />Source-listed year: {year(sourceYear)}<br />Source-listed director: {text(sourceDirector)}</p>
    <p><strong>{provider} response</strong><br />Title: {text(data.title)}<br />Original title: {text(data.original_title)}<br />Release year: {year(data.year)}<br />Director: {directors}</p>
    <p>These values do not confirm a match. A source-listed year may differ from the release year.</p>
  </section>;
}
