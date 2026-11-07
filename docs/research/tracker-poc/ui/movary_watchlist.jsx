import React from "react";
import {sameNormalizedTitle} from "./youtrack_tmdb.js";

export const watchlistForProject = (loaded, project) =>
  project && loaded?.project === project ? loaded.snapshot : null;

// Positive source observations only; absence never means a film is off the list.
export function reconcileMovaryWatchlist(snapshot, films, getId) {
  if (snapshot?.status !== "available" || snapshot.source !== "Movary" ||
      typeof snapshot.observed_at !== "string" || !Number.isFinite(Date.parse(snapshot.observed_at)) ||
      !Array.isArray(snapshot.entries) || !Array.isArray(films)) return null;
  const byId = new Map();
  for (const film of films) {
    const id = getId(film);
    if (!Number.isSafeInteger(id) || id <= 0) continue;
    const matches = byId.get(id) || [];
    matches.push(film);
    byId.set(id, matches);
  }
  const seen = new Set(), rows = [];
  for (const entry of snapshot.entries) {
    const id = entry?.tmdb_id, title = entry?.title, added = entry?.added_at;
    if (!Number.isSafeInteger(id) || id <= 0 || id > 2147483647 || seen.has(id) ||
        (title !== null && (typeof title !== "string" || !title.trim())) ||
        (added !== null && (typeof added !== "string" || !added.trim()))) return null;
    seen.add(id);
    const matches = byId.get(id) || [];
    rows.push({entry, film:matches.length === 1 ? matches[0] : null, ambiguous:matches.length > 1});
  }
  return rows;
}

// Only positive, uniquely matched source observations can select grid records.
export function observedWatchlistKeys(snapshot, films, getId, getKey) {
  const rows = reconcileMovaryWatchlist(snapshot, films, getId);
  return rows === null ? null : new Set(rows.filter(({film}) => film).map(({film}) => getKey(film)));
}

export function MovaryWatchlistBadge({keys, filmKey}) {
  return keys?.has(filmKey) ? <span>On observed Movary watchlist · ID unverified</span> : null;
}

export function MovaryWatchlist({snapshot, films, getId, getKey, getTitle, onSelect, onPrepare, prepareDisabled}) {
  const rows = reconcileMovaryWatchlist(snapshot, films, getId);
  return <section aria-labelledby="movary-watchlist-title">
    <h2 id="movary-watchlist-title">Movary watchlist</h2>
    {rows === null ? <p>Movary watchlist snapshot unavailable for this user or project.</p> : <>
      <p>Observed {snapshot.observed_at}. This is separate from the local POC watchlist; missing entries are unknown. Supplied film IDs are not independently verified.</p>
      {!rows.length ? <p>No entries were present in this observation.</p> : <ul>{rows.map(({entry, film, ambiguous}) => <li key={entry.tmdb_id}>
        {film ? <button type="button" onClick={() => onSelect(film)}>{entry.title || "Title unknown"}</button> : <strong>{entry.title || "Title unknown"}</strong>}
        {entry.added_at && <> · Added at {entry.added_at} (as recorded by Movary)</>}
        {ambiguous ? <p>Multiple tracker records have this supplied ID; review them before proceeding.</p> : !film && <p>Not in the loaded tracker records. {entry.title ? <button type="button" disabled={prepareDisabled} onClick={() => onPrepare(entry)}>Prepare Add film</button> : "A title is needed before adding it."} Preparing does not save or fetch metadata.</p>}
        {film && <small> · Tracker record {getKey(film)}</small>}
        {film && entry.title && !sameNormalizedTitle(entry.title, getTitle(film)) && <p role="alert">The Movary source title and tracker title differ or are unavailable; review film identity.</p>}
      </li>)}</ul>}
    </>}
  </section>;
}
