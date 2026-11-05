import { field } from "./youtrack_filters.js";

export function parseOptionalTmdbId(value) {
  if (typeof value !== "string") throw new Error("TMDB ID must be a positive integer.");
  const text = value.trim();
  if (!text) return null;
  if (!/^[1-9][0-9]*$/.test(text) || Number(text) > 2147483647) throw new Error("TMDB ID must be a positive integer up to 2147483647.");
  return Number(text);
}

export function filmBaseline(film) {
  const fields = (name) => (film.customFields || []).filter((item) => item.name === name);
  const years = fields("FilmIQ Release Year"), genres = fields("FilmIQ Genre");
  const year = years[0]?.value, genre = genres[0]?.value;
  const yearEditable = years.length === 1 && (year === null || (Number.isInteger(year) && year > 0 && year <= 9999));
  const genreEditable = genres.length === 1 && (genre === null || (typeof genre === "string" && (genre === "" || !!genre.trim())));
  return {issueId: film.id, title: film.summary || "", synopsis: film.description || "", state: field(film, "FilmIQ Lifecycle")?.name || "", tmdbId: field(film, "FilmIQ TMDB ID"), releaseYear: yearEditable ? year : null, genre: genreEditable && genre !== "" ? genre : null, yearEditable, genreEditable};
}

export function filmChanges(baseline, draft) {
  const title = draft.title.trim();
  if (!title) throw new Error("Title cannot be blank.");
  const tmdbId = parseOptionalTmdbId(draft.tmdbId);
  if (baseline.tmdbId != null && tmdbId === null) throw new Error("Clearing an existing TMDB ID is not supported in this POC.");
  if (baseline.state && !draft.state) throw new Error("Clearing an existing lifecycle state is not supported in this POC.");
  const changes = {}, customFields = [];
  if (title !== baseline.title) changes.summary = title;
  if (draft.synopsis !== baseline.synopsis) changes.description = draft.synopsis;
  if (draft.state !== baseline.state) customFields.push({name: "FilmIQ Lifecycle", $type: "StateIssueCustomField", value: {name: draft.state}});
  if (tmdbId !== baseline.tmdbId && tmdbId !== null) customFields.push({name: "FilmIQ TMDB ID", $type: "SimpleIssueCustomField", value: tmdbId});
  if (baseline.yearEditable) {
    const text = draft.releaseYear.trim();
    if (text && (!/^[1-9][0-9]{0,3}$/.test(text) || Number(text) > 9999)) throw new Error("Release year must be an integer from 1 to 9999.");
    const year = text ? Number(text) : null;
    if (year !== baseline.releaseYear) customFields.push({name: "FilmIQ Release Year", $type: "SimpleIssueCustomField", value: year});
  }
  if (baseline.genreEditable) {
    const genre = draft.genre === "" ? null : draft.genre;
    if (genre !== null && !genre.trim()) throw new Error("Genre cannot contain only whitespace.");
    if (genre !== baseline.genre) customFields.push({name: "FilmIQ Genre", $type: "SimpleIssueCustomField", value: genre});
  }
  if (customFields.length) changes.customFields = customFields;
  return {changes, tmdbId, idChanged: tmdbId !== baseline.tmdbId};
}

export function hasDuplicateTmdbId(records, id, excludeId = null) {
  if (!Array.isArray(records) || !Number.isInteger(id) || id <= 0) throw new Error("Cannot verify TMDB ID uniqueness.");
  for (const issue of records) {
    if (!issue || typeof issue.id !== "string" || !Array.isArray(issue.customFields)) throw new Error("Cannot verify TMDB ID uniqueness.");
    const fields = issue.customFields.filter((item) => item?.name === "FilmIQ TMDB ID");
    if (fields.length !== 1) throw new Error("Cannot verify TMDB ID uniqueness.");
    const value = fields[0].value;
    if (value != null && (!Number.isInteger(value) || value <= 0)) throw new Error("Cannot verify TMDB ID uniqueness.");
    if (issue.id !== excludeId && value === id) return true;
  }
  return false;
}
