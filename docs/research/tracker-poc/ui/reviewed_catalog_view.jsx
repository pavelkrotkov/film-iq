import React, {useEffect, useState} from "react";
import {readReviewedCatalog, reviewedCatalog} from "./reviewed_catalog.js";
import {TmdbCredits} from "./tmdb_credits.jsx";

// The read is local and read-only. Recheck expiry on a timer and when returning
// to a backgrounded page; no catalog response is stored by the UI.
export function ReviewedCatalog({source, filmId, tmdbId, trackerTitle, host}) {
  const [entry, setEntry] = useState(null);
  const key = JSON.stringify([source, filmId, tmdbId, trackerTitle]);
  useEffect(() => {
    let active = true, timer;
    setEntry(null);
    if (!filmId || !tmdbId) return () => { active = false; };
    const expire = (value) => {
      clearTimeout(timer);
      const remaining = Date.parse(value.expires_at) - Date.now();
      if (remaining <= 0) { if (active) setEntry(null); return; }
      timer = setTimeout(() => expire(value), Math.min(remaining, 2147483647));
    };
    const recheck = () => setEntry((current) => {
      if (!current || current.key !== key) return current;
      return reviewedCatalog(current.value, tmdbId, trackerTitle) ? current : null;
    });
    document.addEventListener("visibilitychange", recheck);
    Promise.resolve().then(() => readReviewedCatalog(source, filmId, host)).then((value) => {
      if (active && reviewedCatalog(value, tmdbId, trackerTitle)) {
        setEntry({key, value});
        expire(value);
      }
    }).catch(() => { /* Optional catalog data remains unknown. */ });
    return () => { active = false; clearTimeout(timer); document.removeEventListener("visibilitychange", recheck); };
  }, [source, filmId, tmdbId, trackerTitle, host, key]);
  const record = entry?.key === key ? reviewedCatalog(entry.value, tmdbId, trackerTitle) : null;
  return <section>
    <h3>Reviewed catalog facts</h3>
    {record ? <>
      <p>Title: {record.title} · Original title: {record.original_title} · Release year: {record.year ?? "unknown"}.</p>
      <p>Director(s): {record.directors.join(", ")} · Runtime: {record.runtime_minutes === null ? "unknown" : `${record.runtime_minutes} minutes`}.</p>
      <p>Source: {record.source} · Observed: {record.observed_at} · Expires: {record.expires_at}.</p>
      <p>{record.attribution}</p>
      <p>A matching title and supplied ID do not independently verify film identity. These facts do not establish streaming availability.</p>
      <TmdbCredits />
    </> : <p>Reviewed catalog facts unavailable.</p>}
  </section>;
}
