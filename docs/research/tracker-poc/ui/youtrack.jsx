import React, { useEffect, useMemo, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import { readDirectReviews, reviewsMatchTitle, safeReviewUrl } from "./direct_reviews.js";
import { field, filterYoutrackFilms, providerObservation, providerFreshness } from "./youtrack_filters.js";
import { loadFilmView, publishFilmBatch } from "./youtrack_loading.js";
export { providerObservation, providerFreshness } from "./youtrack_filters.js";

let locationListener = () => {};
const host = await YTApp.register({ onAppLocationChange: (location) => locationListener(location) });
const fields = "id,idReadable,summary,description,project(id,shortName),customFields(id,name,value(name,text))";
const emptyPreference = { interest_score: null, watchlist: null, watched_at: null, personal_notes: "" };
const states = ["Discovery", "Evaluation", "Watchlist", "Archived"];
export function directReviews(film) {
  const value = field(film, "FilmIQ Direct Review Links");
  return readDirectReviews(value?.text, field(film, "FilmIQ TMDB ID"));
}
export function previewMatchesFilm(preview, filmId) {
  return !!preview && typeof filmId === "string" && preview.issue_id === filmId && !!preview.after;
}
export function providerDescription(observation, key) {
  if (!observation || observation.status === "unknown" || !observation[key]) return "Unknown";
  if (!observation[key].length) return observation.status === "complete" ? "None reported" : "Unknown (partial response)";
  return observation[key].join(", ") + (observation.status === "partial" ? " (partial)" : "");
}

export function parseAppLocation(where) {
  const params = new URLSearchParams(where?.search || "");
  const requested = params.get("project");
  const project = ["FILMPOC", "FILMREAL"].includes(requested) ? requested : "FILMREAL";
  const id = params.get("film");
  return {project, film: id && new RegExp(`^${project}-[1-9]\\d*$`).test(id) ? id : null};
}
async function readPreferences() {
  const response = await host.fetchApp("preferences/all");
  if (!response || typeof response.preferences !== "object" || response.preferences === null) throw new Error("Invalid preference response");
  return Object.fromEntries(Object.entries(response.preferences).filter(([, value]) => value?.recorded && value.preference).map(([id, value]) => [id, value.preference]));
}
const sourceEvidence = (film) => {
  try { return JSON.parse(field(film, "FilmIQ Source Evidence")?.text || "{}"); }
  catch { return {}; }
};
function safeLink(value) {
  try { const url = new URL(value); return ["https:", "http:"].includes(url.protocol) && !url.username && !url.password ? url.href : null; }
  catch { return null; }
}
function ExternalLink({url, label}) {
  return <><a href={url} target="_blank" rel="noreferrer">{label} ↗</a><details><summary>Copy address if opening is blocked</summary><code>{url}</code></details></>;
}

async function getPages(path, query) {
  const rows = [], ids = new Set();
  while (true) {
    const page = await host.fetchYouTrack(path, { query: { ...query, $top: 100, $skip: rows.length } });
    if (!Array.isArray(page)) throw new Error("Unexpected list response");
    if (!page.length) return rows;
    for (const row of page) {
      if (!row.id || ids.has(row.id)) throw new Error("Pagination changed; reload the page.");
      ids.add(row.id);
    }
    rows.push(...page);
  }
}
const getFilms = (project) => getPages("issues", { fields, query: `project: {${project}} sort by: {issue id} asc` });
const getComments = (film) => getPages(`issues/${encodeURIComponent(film.id)}/comments`, { fields: "id,text,author(name)" });

function App() {
  const [project, setProject] = useState(null), [films, setFilms] = useState([]);
  const [preferences, setPreferences] = useState(null), [selected, setSelected] = useState(null);
  const [movary, setMovary] = useState(null), [movaryOnly, setMovaryOnly] = useState(false), [excludeMovaryWatched, setExcludeMovaryWatched] = useState(false);
  const [error, setError] = useState(""), [notice, setNotice] = useState(""), [busy, setBusy] = useState(false), [loadingFilms, setLoadingFilms] = useState(false);
  const [query, setQuery] = useState(""), [stateFilter, setStateFilter] = useState(""), [minimum, setMinimum] = useState("");
  const [watchlistOnly, setWatchlistOnly] = useState(false), [sortInterest, setSortInterest] = useState(false);
  const [provider, setProvider] = useState(""), [genre, setGenre] = useState(""), [freshness, setFreshness] = useState("");
  const [title, setTitle] = useState(""), [synopsis, setSynopsis] = useState(""), [state, setState] = useState(""), [pref, setPref] = useState(emptyPreference);
  const [prefDirty, setPrefDirty] = useState(false), [filmDirty, setFilmDirty] = useState(false);
  const [pendingPreview, setPendingPreview] = useState(null), [pendingNavigation, setPendingNavigation] = useState(null), [discardFailed, setDiscardFailed] = useState(false), [saveUncertain, setSaveUncertain] = useState(false);
  const [comments, setComments] = useState(null), [commentDrafts, setCommentDrafts] = useState({}), [newTitle, setNewTitle] = useState("");
  const sequence = useRef(0), selectedRef = useRef(selected), projectRef = useRef(project);
  selectedRef.current = selected;
  projectRef.current = project;

  async function refresh(target = project) {
    if (!target || target !== projectRef.current) return;
    const run = ++sequence.current;
    setLoadingFilms(true); setPreferences(null); setMovary(null); setError(""); setNotice("");
    try {
      const [personal, watched] = await loadFilmView({
        loadFilms: () => getFilms(target),
        loadPreferences: readPreferences,
        loadWatched: () => host.fetchApp("movary/watched", { query: { project: target } }),
        publishFilms: (loaded) => publishFilmBatch(run, sequence, loaded, setFilms, setLoadingFilms),
      });
      if (run !== sequence.current) return;
      setPreferences(personal.status === "fulfilled" ? personal.value : null);
      setMovary(watched.status === "fulfilled" ? watched.value : null);
      const messages = [];
      if (personal.status === "rejected") {
        setMinimum(""); setWatchlistOnly(false); setSortInterest(false);
        messages.push("Personal preferences are unavailable; preference filters were cleared.");
      }
      if (watched.status !== "fulfilled" || watched.value?.status !== "available") {
        setMovaryOnly(false); setExcludeMovaryWatched(false);
        messages.push("Movary watched data is unavailable; its filter was cleared.");
      }
      setNotice(messages.join(" "));
      return true;
    } catch (e) { if (run === sequence.current) setError(`Could not load films: ${e.message}`); return false; }
    finally { if (run === sequence.current) setLoadingFilms(false); }
  }
  useEffect(() => {
    if (!project) return;
    setFilms([]); setPreferences(null); setMovary(null);
    refresh(project);
    return () => { sequence.current++; };
  }, [project]);
  useEffect(() => {
    let active = true;
    let navigated = false;
    const apply = (where) => {
      if (!active) return;
      const next = parseAppLocation(where);
      setProject(next.project); setSelected(next.film);
    };
    locationListener = (where) => { navigated = true; apply(where); };
    host.navigation.getAppLocation().then((where) => { if (!navigated) apply(where); }).catch(() => { if (!navigated) apply({search: ""}); });
    return () => { active = false; locationListener = () => {}; };
  }, []);
  const film = films.find((item) => item.idReadable === selected);
  useEffect(() => {
    if (!film) return;
    let active = true;
    setPrefDirty(false); setFilmDirty(false);
    setComments(null);
    getComments(film).then((items) => { if (active) setComments(items); }).catch(() => { if (active) setComments(null); });
    return () => { active = false; };
  }, [film?.idReadable]);
  useEffect(() => {
    if (film && !filmDirty) {
      setTitle(film.summary || "");
      setSynopsis(film.description || "");
      setState(field(film, "FilmIQ Lifecycle")?.name || "");
    }
  }, [film, filmDirty]);
  useEffect(() => {
    if (film && !prefDirty) setPref(preferences?.[film.idReadable] || emptyPreference);
  }, [film?.idReadable, preferences, prefDirty]);
  async function selectFilm(id, discard = false) {
    if (pendingPreview || (pendingNavigation && !discard)) return;
    if ((filmDirty || prefDirty) && !discard) { setPendingNavigation({kind: "film", value: id}); return; }
    setFilmDirty(false); setPrefDirty(false);
    setSelected(id);
    const params = new URLSearchParams({ project });
    if (id) params.set("film", id);
    try { await host.navigation.updateAppLocation({ search: params.toString() }); }
    catch { setError("Navigation could not be saved; the current screen may not survive reload."); }
  }
  async function selectProject(next, discard = false) {
    if (pendingPreview || (pendingNavigation && !discard)) return;
    if ((filmDirty || prefDirty) && !discard) { setPendingNavigation({kind: "project", value: next}); return; }
    setFilmDirty(false); setPrefDirty(false);
    setSelected(null); setProject(next);
    try { await host.navigation.updateAppLocation({ search: new URLSearchParams({project: next}).toString() }); }
    catch { setError("Project navigation could not be saved; the current screen may not survive reload."); }
  }
  const providers = [...new Set(films.flatMap((item) => {
    const observation = providerObservation(item);
    return observation?.status !== "unknown" ? observation?.subscription || [] : [];
  }))].sort();
  const genres = [...new Set(films.map((item) => field(item, "FilmIQ Genre")).filter((value) => typeof value === "string" && value))].sort();
  const visible = useMemo(() => filterYoutrackFilms(films, {preferences, query, stateFilter, minimum, watchlistOnly, sortInterest, movaryOnly, excludeMovaryWatched, movary, provider, genre, freshness}), [films, preferences, query, stateFilter, minimum, watchlistOnly, sortInterest, movaryOnly, excludeMovaryWatched, movary, provider, genre, freshness]);
  async function saveFilm(event) {
    event.preventDefault(); if (!title.trim()) { setError("Title cannot be blank."); return; } setBusy(true); setError("");
    try {
      const changes = { summary: title.trim(), description: synopsis };
      if (state) changes.customFields = [{ name: "FilmIQ Lifecycle", $type: "StateIssueCustomField", value: { name: state } }];
      await host.fetchYouTrack(`issues/${encodeURIComponent(film.id)}`, { method: "POST", body: changes });
      const refreshed = await refresh();
      if (refreshed) { setFilmDirty(false); setNotice("Film changes saved in YouTrack."); }
      else setError("Film changes saved, but refresh failed. Reload to confirm the displayed record.");
    } catch (e) { setError(`Could not save film: ${e.message}`); }
    finally { setBusy(false); }
  }
  async function savePreference(event) {
    event.preventDefault(); if (preferences === null || !film) return; setBusy(true); setError(""); const target = film.idReadable;
    try {
      const preview = await host.fetchApp("preferences/preview", { method: "POST", body: { issue_id: target, preference: pref } });
      if (!previewMatchesFilm(preview, target)) throw new Error("Invalid preview");
      setDiscardFailed(false); setSaveUncertain(false);
      if (selectedRef.current !== target) {
        try {
          await host.fetchApp("preferences/discard", { method: "POST", body: preview });
          setNotice("The selected film changed; the earlier preference preview was discarded.");
        } catch {
          setPendingPreview(preview); setDiscardFailed(true);
          setError("The selected film changed and the earlier preview could not be cleared.");
        }
        return;
      }
      setPendingPreview(preview);
    } catch (e) { setError(`Could not prepare preference preview: ${e.message}`); }
    finally { setBusy(false); }
  }
  async function confirmPreference() {
    if (!previewMatchesFilm(pendingPreview, selectedRef.current)) { setError("The selected film changed; cancel and preview again."); return; }
    setBusy(true); setError(""); let saved = false; const target = pendingPreview.issue_id;
    try {
      await host.fetchApp("preferences/confirm", { method: "POST", body: pendingPreview });
      saved = true;
      setPendingPreview(null); setDiscardFailed(false); setSaveUncertain(false);
      setPreferences(await readPreferences());
      if (selectedRef.current === target) setPrefDirty(false);
      setNotice(`Local preference for ${target} saved; Movary was not changed.`);
    } catch (e) {
      if (saved) setError(`Preference saved, but refresh failed: ${e.message}`);
      else { setSaveUncertain(true); setDiscardFailed(true); setError("Save may have completed. Close this preview, then open a new preview to compare the server's Before value."); }
    }
    finally { setBusy(false); }
  }
  async function discardPreference() {
    setBusy(true); setError("");
    try {
      await host.fetchApp("preferences/discard", { method: "POST", body: pendingPreview });
      setPendingPreview(null); setDiscardFailed(false);
      setNotice(saveUncertain ? "Preview closed; open a new preview to compare the server's Before value." : "Preference preview discarded; no preference was saved.");
      setSaveUncertain(false);
    } catch { setDiscardFailed(true); setError("Cancellation could not clear the server preview; retry or close it locally."); }
    finally { setBusy(false); }
  }
  async function addComment(event) {
    event.preventDefault();
    const target = film, text = commentDrafts[target.idReadable] || "";
    if (!text.trim()) return;
    setBusy(true);
    try {
      await host.fetchYouTrack(`issues/${encodeURIComponent(target.id)}/comments`, { method: "POST", body: { text } });
      setCommentDrafts((drafts) => ({ ...drafts, [target.idReadable]: "" }));
      const updated = await getComments(target);
      if (selectedRef.current === target.idReadable) setComments(updated);
    } catch (e) { setError(`Comment may not have saved: ${e.message}`); }
    finally { setBusy(false); }
  }
  async function addFilm(event) {
    event.preventDefault(); if (!newTitle.trim()) return;
    setBusy(true); setError("");
    try {
      const projectInfo = await host.fetchYouTrack(`admin/projects/${project}`, { query: { fields: "id" } });
      const created = await host.fetchYouTrack("issues", { method: "POST", query: { fields: "idReadable" }, body: { project: { id: projectInfo.id }, summary: newTitle.trim() } });
      setNewTitle(""); await refresh(); await selectFilm(created.idReadable);
    } catch (e) { setError(`Creation may be incomplete; reload before retrying: ${e.message}`); }
    finally { setBusy(false); }
  }
  function changePreference(values) { setPref((current) => ({...current, ...values})); setPrefDirty(true); }
  const evidence = film ? sourceEvidence(film) : {};
  const sourceLinks = Array.isArray(evidence?.links) ? evidence.links.filter((item) => item && typeof item === "object") : [];
  const reviews = film ? directReviews(film) : null;
  const staleReviews = film && reviews?.length && !reviewsMatchTitle(reviews, film.summary);
  const observation = film ? providerObservation(film) : null;
  const locked = busy || loadingFilms || !!pendingPreview || !!pendingNavigation;
  const preferenceLabel = (value) => value === null ? "unknown" : value === true ? "yes" : value === false ? "no" : value;
  return <>
    <header><button className="brand" type="button" disabled={locked} onClick={() => selectFilm(null)} style={{background:"transparent",color:"inherit",padding:0}}>FILM <span> / </span> LAB</button><nav>Discovery · Watchlist · Administration</nav></header>
    <main>
      <div className="intro"><div><span className="eyebrow">YOUTRACK · LOCAL POC</span><h1>Film discovery</h1><p>Shared film records and separate personal preferences.</p></div></div>
      <div className="project"><label>Project<select value={project || ""} disabled={locked} onChange={(e) => selectProject(e.target.value)}><option value="" disabled>Loading project…</option><option value="FILMREAL">Film collection</option><option value="FILMPOC">Synthetic test films</option></select></label><button disabled={locked || !project} onClick={() => refresh()}>Reload</button><a href="/issues" target="_blank" rel="noreferrer">Open tracker administration ↗</a></div>
      {error && <p role="alert">{error}</p>}{notice && <p className="notice">{notice}</p>}
      {pendingNavigation && <section aria-labelledby="discard-title"><h2 id="discard-title">Discard unsaved edits?</h2><p>Your film and preference drafts have not been saved.</p><button disabled={busy} autoFocus onClick={() => setPendingNavigation(null)}>Keep editing</button><button disabled={busy} onClick={() => {const target = pendingNavigation; setPendingNavigation(null); if (target.kind === "film") selectFilm(target.value, true); else selectProject(target.value, true);}}>Discard and continue</button></section>}
      {pendingPreview && <section aria-labelledby="preference-preview-title"><h2 id="preference-preview-title">Review preference changes</h2><p>Film: {pendingPreview.issue_id}</p><p>Interest: {preferenceLabel((pendingPreview.before || emptyPreference).interest_score)} → {preferenceLabel(pendingPreview.after.interest_score)}</p><p>Watchlist: {preferenceLabel((pendingPreview.before || emptyPreference).watchlist)} → {preferenceLabel(pendingPreview.after.watchlist)}</p><p>Watched date: {preferenceLabel((pendingPreview.before || emptyPreference).watched_at)} → {preferenceLabel(pendingPreview.after.watched_at)}</p><p>Notes before: {(pendingPreview.before || emptyPreference).personal_notes || "(empty)"}</p><p>Notes after: {pendingPreview.after.personal_notes || "(empty)"}</p><button disabled={busy} autoFocus onClick={discardPreference}>Cancel preview</button><button disabled={busy || saveUncertain || !previewMatchesFilm(pendingPreview, selected)} onClick={confirmPreference}>Save local preference</button>{discardFailed && <><p>The server preview may remain until another preview or app removal. Draft notes are not stored in it.</p><button disabled={busy} onClick={() => {setPendingPreview(null); setDiscardFailed(false); setNotice(saveUncertain ? "Preview closed locally; the save outcome and server preview remain unverified. Open a new preview to compare the server's Before value." : "Preview closed locally; the server preview may remain."); setSaveUncertain(false);}}>Close preview locally</button></>}</section>}
      {film ? <section>
        <button disabled={locked} onClick={() => selectFilm(null)}>← Back to films</button>
        <h2>{film.summary}</h2><p>{film.idReadable} · {field(film, "FilmIQ Source Year") ? `Source-listed year ${field(film, "FilmIQ Source Year")}` : "Release year unknown"}</p>
        <p>{field(film, "FilmIQ Director") ? `Source-listed director: ${field(film, "FilmIQ Director")}` : "Director unknown"}</p>
        <p>{movary?.status === "available" && movary?.films?.[film.idReadable]?.watched ? `Watched in Movary (snapshot ${movary.observed_at || "time unknown"}).` : "Movary watched status unknown."}</p>
        <h3>Streaming availability</h3>
        <p>{observation ? `Synthetic observation: ${observation.status}. Checked ${observation.checked_at || "time unknown"}.` : "Availability unknown."}</p>
        <p>Subscriptions: {providerDescription(observation, "subscription")}. Rentals: {providerDescription(observation, "rent")}.</p>
        <form onSubmit={saveFilm}><label>Title<input value={title} required disabled={locked} onChange={(e) => {setTitle(e.target.value); setFilmDirty(true);}} /></label><label>Synopsis<textarea value={synopsis} disabled={locked} onChange={(e) => {setSynopsis(e.target.value); setFilmDirty(true);}} /></label><label>Lifecycle<select value={state} disabled={locked} onChange={(e) => {setState(e.target.value); setFilmDirty(true);}}><option value="">Unknown</option>{states.map((s) => <option key={s}>{s}</option>)}</select></label><button disabled={locked}>Save film</button></form>
        <p>Changing a title does not independently verify the saved external identity or update its original source provenance.</p>
        <p>Critic score: {field(film, "FilmIQ Critic Score") ?? "Unknown"}. {field(film, "FilmIQ Critic Summary")?.text || "Critic summary unavailable."}</p>
        <h3>Personal POC preferences</h3>
        {preferences === null ? <p>Preferences are loading or unavailable.</p> : <form onSubmit={savePreference}>
          <label>Interest (1–10)<input type="number" min="1" max="10" disabled={locked} value={pref.interest_score ?? ""} onChange={(e) => changePreference({ interest_score: e.target.value === "" ? null : Number(e.target.value) })} /></label>
          <label>Local POC watchlist<select disabled={locked} value={pref.watchlist === null ? "unknown" : pref.watchlist ? "yes" : "no"} onChange={(e) => changePreference({ watchlist: e.target.value === "unknown" ? null : e.target.value === "yes" })}><option value="unknown">Unknown</option><option value="yes">Yes</option><option value="no">No</option></select></label>
          <label>Watched timestamp (UTC)<input type="datetime-local" disabled={locked} value={pref.watched_at ? pref.watched_at.slice(0, 16) : ""} onChange={(e) => changePreference({ watched_at: e.target.value ? new Date(`${e.target.value}Z`).toISOString() : null })} /></label>
          <label>Personal notes<textarea disabled={locked} value={pref.personal_notes} onChange={(e) => changePreference({ personal_notes: e.target.value })} /></label><button disabled={locked}>Preview preference changes</button><p className="notice">Local experiment only; Movary remains authoritative.</p>
        </form>}
        <h3>Source evidence</h3>{sourceLinks.length ? <ul>{sourceLinks.map((item, index) => { const url = safeLink(item.url); return <li key={index}>{url ? <ExternalLink url={url} label={item.source_id || "Source"} /> : "Source link unavailable"} · {item.kind || "type unknown"} · lineage: {item.lineage_kind || "unknown"}</li>; })}</ul> : <p>Accepted source evidence unavailable.</p>}
        <h3>Direct reviews and aggregators</h3>{staleReviews ? <p>The film title differs from the reviewed source title; links are hidden until revalidated.</p> : reviews?.length ? <ul>{reviews.map((link, index) => <li key={index}><ExternalLink url={safeReviewUrl(link.url)} label={link.provider} /> · {link.type === "individual_critic_review" ? "Individual critic review" : "Review aggregator title page"} · checked {link.checked_at}<p>Page title: {link.identity_evidence.source_page_title}; directors: {link.identity_evidence.source_directors.join(", ")}. {link.identity_evidence.identity_caveat} {link.identity_evidence.details_note}</p></li>)}</ul> : <p>Direct review links unavailable; coverage is unknown.</p>}
        <h3>Comments</h3>{comments === null ? <p>Comments unavailable.</p> : <ul>{comments.map((item) => <li key={item.id}>{item.author?.name || "Unknown"}: {item.text}</li>)}</ul>}
        <form onSubmit={addComment}><label>Add comment<textarea disabled={locked} value={commentDrafts[film.idReadable] || ""} onChange={(e) => setCommentDrafts((drafts) => ({...drafts, [film.idReadable]: e.target.value}))} /></label><button disabled={locked}>Add comment</button></form>
        <a href={`/issue/${film.idReadable}`} target="_blank" rel="noreferrer">View tracker record and history ↗</a>
      </section> : <section>
        <div className="filters">
          <label>Search<input value={query} onChange={(e) => setQuery(e.target.value)} /></label>
          <label>Lifecycle<select value={stateFilter} onChange={(e) => setStateFilter(e.target.value)}><option value="">All</option>{states.map((s) => <option key={s}>{s}</option>)}</select></label>
          <label>Genre<select value={genre} onChange={(e) => setGenre(e.target.value)}><option value="">All genres</option>{genres.map((g) => <option key={g}>{g}</option>)}</select></label>
          <label>Provider<select value={provider} onChange={(e) => setProvider(e.target.value)}><option value="">All providers</option>{providers.map((p) => <option key={p}>{p}</option>)}</select></label>
          <label>Availability freshness<select value={freshness} onChange={(e) => setFreshness(e.target.value)}><option value="">Any freshness</option><option value="recent">Checked within 7 days</option><option value="stale">Older than 7 days</option><option value="unknown">Unknown</option></select></label>
          <label>Minimum interest<input type="number" min="1" max="10" value={minimum} disabled={preferences === null && !minimum} onChange={(e) => setMinimum(e.target.value)} /></label>
          <label><input type="checkbox" checked={watchlistOnly} disabled={preferences === null && !watchlistOnly} onChange={(e) => setWatchlistOnly(e.target.checked)} /> Watchlist only</label>
          <label><input type="checkbox" checked={movaryOnly} disabled={movary?.status !== "available" && !movaryOnly} onChange={(e) => {setMovaryOnly(e.target.checked); if (e.target.checked) setExcludeMovaryWatched(false);}} /> Watched in Movary</label>
          <label><input type="checkbox" checked={excludeMovaryWatched} disabled={movary?.status !== "available" && !excludeMovaryWatched} onChange={(e) => {setExcludeMovaryWatched(e.target.checked); if (e.target.checked) setMovaryOnly(false);}} /> Exclude known watched in Movary</label>
          <label><input type="checkbox" checked={sortInterest} disabled={preferences === null && !sortInterest} onChange={(e) => setSortInterest(e.target.checked)} /> Sort by interest</label>
        </div>
        <h2>Discovery · {visible.length}</h2><div className="grid">{visible.map((item) => <button className="card" key={item.id} disabled={locked} onClick={() => selectFilm(item.idReadable)}><span className="poster">Artwork unavailable</span><strong>{item.summary}</strong><small>{field(item, "FilmIQ Source Year") || "Year unknown"} · Interest {preferences?.[item.idReadable]?.interest_score ?? "unknown"} · Critic {field(item, "FilmIQ Critic Score") ?? "unknown"}</small><small>{field(item, "FilmIQ Lifecycle")?.name || "State unknown"} · {movary?.status === "available" && movary?.films?.[item.idReadable]?.watched ? "Watched in Movary" : "Watched unknown"}</small><small>Subscriptions: {providerDescription(providerObservation(item), "subscription")}</small></button>)}</div>
        <form onSubmit={addFilm}><label>Add film title<input disabled={locked} value={newTitle} onChange={(e) => setNewTitle(e.target.value)} /></label><button disabled={locked || !project}>Add film</button></form>
      </section>}
    </main>
  </>;
}

if (typeof document !== "undefined") createRoot(document.getElementById("root")).render(<App />);
