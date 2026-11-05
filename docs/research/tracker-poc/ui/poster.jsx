import React, {useEffect, useState} from 'react';
import {safePosterUrl} from './youtrack_tmdb.js';

// Cache-enabled builds fetch poster bytes without the HTTP cache. Object URLs
// are revoked on change/unmount; a blocked fetch leaves the placeholder.
export function Poster({url, alt, loading, transient = false, fallback = 'Artwork unavailable'}) {
  const [entry, setEntry] = useState(null);
  useEffect(() => {
    if (!transient || !url) return;
    const safe = safePosterUrl(url);
    if (!safe) return;
    const controller = new AbortController();
    let active = true, objectUrl = null;
    void (async () => {
      try {
        const response = await fetch(safe, {cache:'no-store', mode:'cors', credentials:'omit', referrerPolicy:'no-referrer', redirect:'error', signal:controller.signal});
        if (!response.ok) throw new Error('Poster unavailable');
        const blob = await response.blob();
        if (!blob.type.startsWith('image/')) throw new Error('Invalid poster');
        objectUrl = URL.createObjectURL(blob);
        if (active) setEntry({url, objectUrl});
        else URL.revokeObjectURL(objectUrl);
      } catch { /* CSP, CORS, or network failure leaves a placeholder. */ }
    })();
    return () => { active = false; controller.abort(); if (objectUrl) URL.revokeObjectURL(objectUrl); };
  }, [url, transient]);
  const src = transient ? entry && entry.url === url ? entry.objectUrl : null : url;
  return src ? <img src={src} alt={alt} loading={loading} onError={transient ? () => {URL.revokeObjectURL(src); setEntry(null);} : undefined} /> : fallback;
}
