import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";

const host = await YTApp.register();
const fields = "id,idReadable,summary,description,project(id,shortName),customFields(id,name,value(name,text))";
const emptyPreference = { interest_score: null, watchlist: null, watched_at: null, personal_notes: "" };
const states = ["Discovery", "Evaluation", "Watchlist", "Archived"];
const field = (film, name) => film.customFields?.find((item) => item.name === name)?.value ?? null;
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
  try { const url = new URL(value); return ["https:", "http:"].includes(url.protocol) ? url.href : null; }
  catch { return null; }
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
  const [project, setProject] = useState("FILMREAL"), [films, setFilms] = useState([]);
  const [preferences, setPreferences] = useState(null), [selected, setSelected] = useState(null);
  const [movary, setMovary] = useState(null), [movaryOnly, setMovaryOnly] = useState(false);
  const [error, setError] = useState(""), [notice, setNotice] = useState(""), [busy, setBusy] = useState(false);
  const [query, setQuery] = useState(""), [stateFilter, setStateFilter] = useState(""), [minimum, setMinimum] = useState("");
  const [watchlistOnly, setWatchlistOnly] = useState(false), [sortInterest, setSortInterest] = useState(false);
  const [synopsis, setSynopsis] = useState(""), [state, setState] = useState(""), [pref, setPref] = useState(emptyPreference);
  const [comments, setComments] = useState([]), [newComment, setNewComment] = useState(""), [newTitle, setNewTitle] = useState("");

  async function refresh() {
    setBusy(true); setError("");
    try {
      setFilms(await getFilms(project));
      try { setPreferences(await readPreferences()); }
      catch { setPreferences(null); setNotice("Personal preferences are unavailable; they are not treated as empty."); }
      try { setMovary(await host.fetchApp("movary/watched")); }
      catch { setMovary(null); }
    } catch (e) { setError(`Could not load films: ${e.message}`); }
    finally { setBusy(false); }
  }
  useEffect(() => { refresh(); }, [project]);
  useEffect(() => {
    host.navigation.getAppLocation().then((where) => {
      const params = new URLSearchParams(where.search);
      const issue = params.get("film"), sourceProject = params.get("project");
      if (["FILMPOC", "FILMREAL"].includes(sourceProject)) setProject(sourceProject);
      if (issue) setSelected(issue);
    }).catch(() => {});
  }, []);
  const film = films.find((item) => item.idReadable === selected);
  useEffect(() => {
    if (!film) return;
    setSynopsis(film.description || "");
    setState(field(film, "FilmIQ Lifecycle")?.name || "");
    setPref(preferences?.[film.idReadable] || emptyPreference);
    getComments(film).then(setComments).catch(() => setComments(null));
  }, [film, preferences]);
  async function selectFilm(id) {
    setSelected(id);
    const params = new URLSearchParams({ project });
    if (id) params.set("film", id);
    await host.navigation.updateAppLocation({ search: params.toString() });
  }
  const visible = useMemo(() => {
    const matching = films.filter((item) => {
      const personal = preferences?.[item.idReadable];
      if (query && !item.summary.toLowerCase().includes(query.toLowerCase())) return false;
      if (stateFilter && field(item, "FilmIQ Lifecycle")?.name !== stateFilter) return false;
      if (minimum && (personal?.interest_score == null || personal.interest_score < Number(minimum))) return false;
      if (watchlistOnly && personal?.watchlist !== true) return false;
      if (movaryOnly && movary?.films?.[item.idReadable]?.watched !== true) return false;
      return true;
    });
    if (sortInterest) matching.sort((a, b) => (preferences?.[b.idReadable]?.interest_score ?? -1) - (preferences?.[a.idReadable]?.interest_score ?? -1));
    return matching;
  }, [films, preferences, query, stateFilter, minimum, watchlistOnly, sortInterest, movaryOnly, movary]);
  async function saveFilm(event) {
    event.preventDefault(); setBusy(true); setError("");
    try {
      const changes = { description: synopsis };
      if (state) changes.customFields = [{ name: "FilmIQ Lifecycle", $type: "StateIssueCustomField", value: { name: state } }];
      await host.fetchYouTrack(`issues/${encodeURIComponent(film.id)}`, { method: "POST", body: changes });
      await refresh(); setNotice("Film changes saved in YouTrack.");
    } catch (e) { setError(`Could not save film: ${e.message}`); }
    finally { setBusy(false); }
  }
  async function savePreference(event) {
    event.preventDefault(); setBusy(true); setError("");
    try {
      const preview = await host.fetchApp("preferences/preview", { method: "POST", body: { issue_id: film.idReadable, preference: pref } });
      const before = preview.before || emptyPreference;
      const label = (v) => v === null ? "unknown" : v === true ? "yes" : v === false ? "no" : v;
      const prompt = `Review personal POC preference change:\nInterest: ${label(before.interest_score)} → ${label(preview.after.interest_score)}\nWatchlist: ${label(before.watchlist)} → ${label(preview.after.watchlist)}\nWatched date: ${label(before.watched_at)} → ${label(preview.after.watched_at)}\nNotes before: ${before.personal_notes || "(empty)"}\nNotes after: ${preview.after.personal_notes || "(empty)"}\n\nSave this local POC preference?`;
      if (window.confirm(prompt)) {
        await host.fetchApp("preferences/confirm", { method: "POST", body: preview });
        setPreferences(await readPreferences());
        setNotice("Local preference saved; Movary was not changed.");
      }
    } catch (e) { setError(`Could not save preferences: ${e.message}`); }
    finally { setBusy(false); }
  }
  async function addComment(event) {
    event.preventDefault(); if (!newComment.trim()) return;
    try {
      await host.fetchYouTrack(`issues/${encodeURIComponent(film.id)}/comments`, { method: "POST", body: { text: newComment } });
      setNewComment("");
      setComments(await getComments(film));
    } catch (e) { setError(`Comment may not have saved: ${e.message}`); }
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
  const evidence = film ? sourceEvidence(film) : {};
  return <>
    <header><a className="brand" href="#">FILM <span> / </span> LAB</a><nav>Discovery · Watchlist · Administration</nav></header>
    <main>
      <div className="intro"><div><span className="eyebrow">YOUTRACK · LOCAL POC</span><h1>Film discovery</h1><p>Shared film records and separate personal preferences.</p></div></div>
      <div className="project"><label>Project<select value={project} onChange={(e) => { setSelected(null); setProject(e.target.value); }}><option value="FILMREAL">Film collection</option><option value="FILMPOC">Synthetic test films</option></select></label><button disabled={busy} onClick={refresh}>Reload</button><a href="/issues" target="_blank" rel="noreferrer">Open tracker administration ↗</a></div>
      {error && <p role="alert">{error}</p>}{notice && <p className="notice">{notice}</p>}
      {film ? <section>
        <button onClick={() => selectFilm(null)}>← Back to films</button>
        <h2>{film.summary}</h2><p>{film.idReadable} · {field(film, "FilmIQ Source Year") ? `Source-listed year ${field(film, "FilmIQ Source Year")}` : "Release year unknown"}</p>
        <p>{field(film, "FilmIQ Director") ? `Source-listed director: ${field(film, "FilmIQ Director")}` : "Director unknown"}</p>
        <p>{movary?.films?.[film.idReadable]?.watched ? `Watched in Movary (snapshot ${movary.observed_at || "time unknown"}).` : "Movary watched status unknown."}</p>
        <form onSubmit={saveFilm}><label>Synopsis<textarea value={synopsis} onChange={(e) => setSynopsis(e.target.value)} /></label><label>Lifecycle<select value={state} onChange={(e) => setState(e.target.value)}><option value="">Unknown</option>{states.map((s) => <option key={s}>{s}</option>)}</select></label><button disabled={busy}>Save film</button></form>
        <h3>Personal POC preferences</h3>
        {preferences === null ? <p>Preferences unavailable.</p> : <form onSubmit={savePreference}>
          <label>Interest (1–10)<input type="number" min="1" max="10" value={pref.interest_score ?? ""} onChange={(e) => setPref({ ...pref, interest_score: e.target.value === "" ? null : Number(e.target.value) })} /></label>
          <label>Local POC watchlist<select value={pref.watchlist === null ? "unknown" : pref.watchlist ? "yes" : "no"} onChange={(e) => setPref({ ...pref, watchlist: e.target.value === "unknown" ? null : e.target.value === "yes" })}><option value="unknown">Unknown</option><option value="yes">Yes</option><option value="no">No</option></select></label>
          <label>Watched timestamp (UTC)<input type="datetime-local" value={pref.watched_at ? pref.watched_at.slice(0, 16) : ""} onChange={(e) => setPref({ ...pref, watched_at: e.target.value ? new Date(`${e.target.value}Z`).toISOString() : null })} /></label>
          <label>Personal notes<textarea value={pref.personal_notes} onChange={(e) => setPref({ ...pref, personal_notes: e.target.value })} /></label><button disabled={busy}>Preview preference changes</button><p className="notice">Local experiment only; Movary remains authoritative.</p>
        </form>}
        <h3>Source evidence</h3>{evidence.links?.length ? <ul>{evidence.links.map((item, index) => { const url = safeLink(item.url); return <li key={index}>{url ? <a href={url} target="_blank" rel="noreferrer">{item.source_id || "Source"} ↗</a> : "Source link unavailable"} · {item.kind || "type unknown"} · lineage: {item.lineage_kind || "unknown"}</li>; })}</ul> : <p>Accepted source evidence unavailable.</p>}
        <h3>Comments</h3>{comments === null ? <p>Comments unavailable.</p> : <ul>{comments.map((item) => <li key={item.id}>{item.author?.name || "Unknown"}: {item.text}</li>)}</ul>}
        <form onSubmit={addComment}><label>Add comment<textarea value={newComment} onChange={(e) => setNewComment(e.target.value)} /></label><button>Add comment</button></form>
        <a href={`/issue/${film.idReadable}`} target="_blank" rel="noreferrer">View tracker record and history ↗</a>
      </section> : <section>
        <div className="filters"><label>Search<input value={query} onChange={(e) => setQuery(e.target.value)} /></label><label>Lifecycle<select value={stateFilter} onChange={(e) => setStateFilter(e.target.value)}><option value="">All</option>{states.map((s) => <option key={s}>{s}</option>)}</select></label><label>Minimum interest<input type="number" min="1" max="10" value={minimum} onChange={(e) => setMinimum(e.target.value)} /></label><label><input type="checkbox" checked={watchlistOnly} onChange={(e) => setWatchlistOnly(e.target.checked)} /> Watchlist only</label><label><input type="checkbox" checked={movaryOnly} onChange={(e) => setMovaryOnly(e.target.checked)} /> Watched in Movary</label><label><input type="checkbox" checked={sortInterest} onChange={(e) => setSortInterest(e.target.checked)} /> Sort by interest</label></div>
        <h2>Discovery · {visible.length}</h2><div className="grid">{visible.map((item) => <button className="card" key={item.id} onClick={() => selectFilm(item.idReadable)}><span className="poster">Artwork unavailable</span><strong>{item.summary}</strong><small>{field(item, "FilmIQ Source Year") || "Year unknown"} · Interest {preferences?.[item.idReadable]?.interest_score ?? "unknown"}</small><small>{field(item, "FilmIQ Lifecycle")?.name || "State unknown"} · {movary?.films?.[item.idReadable]?.watched ? "Watched in Movary" : "Watched unknown"} · Streaming unknown</small></button>)}</div>
        <form onSubmit={addFilm}><label>Add film title<input value={newTitle} onChange={(e) => setNewTitle(e.target.value)} /></label><button disabled={busy}>Add film</button></form>
      </section>}
    </main>
  </>;
}

createRoot(document.getElementById("root")).render(<App />);
