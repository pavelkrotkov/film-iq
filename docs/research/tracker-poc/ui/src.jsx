import React, { useEffect, useMemo, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  filterFilms,
  providers,
  syntheticAvailability,
} from "./film_filters.js";
import { BATCH_LIMIT, chooseBatch, mergeResult, runBatch, tmdbId } from "./live_batch.js";
import { fetchRatings } from "./mdblist_ui.js";
import { clearSavedDraft, currentComments, setCommentDraft } from "./comment_drafts.js";
import { emptyPreference, markPreferenceSaved, mergeFilmDraft, syncPreferenceDraft } from "./preference_draft.js";

const api = "http://localhost:15173/api";
function ProviderBadges({ film }) {
  const services = providers(film);
  if (services === null) return <span>Availability unknown</span>;
  if (film.live?.availability?.status === "partial" && !services.length)
    return <span>Availability incomplete</span>;
  if (!services.length) return <><span>No subscriptions reported</span>{film.live?.availability_attempt && <span>Latest check incomplete</span>}</>;
  return <>{services.map((name) => <span key={name}>{name}</span>)}{film.live?.availability?.status === "partial" && <span>Partial</span>}{film.live?.availability_attempt && <span>Latest check incomplete</span>}</>;
}

function Credits() {
  return <section><h4>Credits</h4><p><a href="https://www.themoviedb.org/" target="_blank" rel="noreferrer"><img src="https://www.themoviedb.org/assets/v4/logos/v2/blue_long_2-9665a76b1ae401a510ec1e0ca40ddcb3b0cfe45f1d51b77a308fea0845885648.svg" alt="TMDB" width="120" /></a> This product uses the TMDB API but is not endorsed or certified by TMDB. Watch-provider data: <a href="https://www.justwatch.com/" target="_blank" rel="noreferrer">JustWatch</a>.</p></section>;
}

function SourceEvidence({ film }) {
  let evidence;
  try {
    evidence = JSON.parse(film.fields["POC Evidence"] || "null");
  } catch {
    return <p>Source evidence unavailable.</p>;
  }
  const links = Array.isArray(evidence?.links) ? evidence.links : [];
  return <section>
    <h3>Source evidence</h3>
    {film.fields["POC Identity Provenance"] && <p>Identity provenance: {film.fields["POC Identity Provenance"]}</p>}
    {film.fields["POC Source Year"] && <p>Source-listed year: {film.fields["POC Source Year"]} (not independently verified).</p>}
    {links.length ? <ul>{links.map((item, index) => {
      let url;
      try { const parsed = new URL(item.url); if (parsed.protocol === "https:" || parsed.protocol === "http:") url = parsed.href; } catch { /* Invalid source links stay unavailable. */ }
      return <li key={item.entry_id || index}>{url ? <a href={url} target="_blank" rel="noreferrer">{item.source_id || "Source"} ↗</a> : "Source link unavailable"}{item.kind ? ` · ${item.kind}` : ""}{item.rank ? ` · rank ${item.rank}` : ""}{item.lineage_kind ? ` · ${item.lineage_kind}` : ""}</li>;
    })}</ul> : <p>Source evidence unknown.</p>}
    <p>These links identify source evidence; a list or ballot is not necessarily an individual review.</p>
  </section>;
}

async function request(path, method = "GET", body) {
  const response = await fetch(api + path, {
    method,
    credentials: "include",
    headers: body ? { "Content-Type": "application/json" } : {},
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!response.ok) throw new Error(`Kaneo returned HTTP ${response.status}`);
  return response.json();
}

async function preferenceRequest(path, method = "GET", body) {
  const response = await fetch("http://localhost:15175" + path, {
    method,
    credentials: "include",
    headers: body ? { "Content-Type": "application/json" } : {},
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!response.ok)
    throw new Error(`Preference bridge returned HTTP ${response.status}`);
  return response.json();
}

async function load(project) {
  const id = encodeURIComponent(project);
  const columns = await request(`/column/${id}`);
  if (!Array.isArray(columns) || !columns.length)
    throw new Error("The project has no usable lifecycle columns.");
  const rows = await request(`/custom-field/project/${id}/values`);
  const values = new Map();
  for (const row of rows) {
    const record = values.get(row.taskId) || {};
    record[row.fieldName] = row.value;
    values.set(row.taskId, record);
  }
  const films = [];
  let page = 1,
    pages = 1,
    total;
  while (page <= pages) {
    const result = await request(`/task/tasks/${id}?limit=100&page=${page}`);
    pages = result.pagination.totalPages;
    if (total !== undefined && total !== result.pagination.total)
      throw new Error("The board changed while loading; try again.");
    total = result.pagination.total;
    for (const column of result.data.columns) films.push(...column.tasks);
    films.push(...result.data.archivedTasks, ...result.data.plannedTasks);
    page++;
  }
  if (films.length !== total || new Set(films.map((f) => f.id)).size !== total)
    throw new Error("The board response was incomplete.");
  return {
    films: films.map((film) => ({ ...film, fields: values.get(film.id) || {} })),
    states: Object.fromEntries([
      ...columns.map((column) => [column.slug, column.name]),
      ["planned", "Planned"],
      ["archived", "Archived"],
    ]),
    defaultState: columns[0].slug,
  };
}

function selectedId() {
  return new URLSearchParams(location.hash.slice(1)).get("film");
}

function App() {
  const [project, setProject] = useState(
    new URLSearchParams(location.search).get("project") || "",
  );
  const [films, setFilms] = useState([]),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  const [states, setStates] = useState({}),
    [defaultState, setDefaultState] = useState("");
  const [selected, setSelected] = useState(selectedId),
    [query, setQuery] = useState(""),
    [provider, setProvider] = useState("");
  const [preferences, setPreferences] = useState(null),
    [preferenceDraft, setPreferenceDraft] = useState({filmId: null, value: emptyPreference, dirty: false}),
    [watchlistOnly, setWatchlistOnly] = useState(false),
    [sortInterest, setSortInterest] = useState(false);
  const [movary, setMovary] = useState(null),
    [movaryOnly, setMovaryOnly] = useState(false);
  const [minimum, setMinimum] = useState(""),
    [genre, setGenre] = useState(""),
    [lifecycle, setLifecycle] = useState(""),
    [watched, setWatched] = useState(""),
    [freshnessFilter, setFreshnessFilter] = useState("");
  const [filmDraft, setFilmDraft] = useState({description: "", status: ""}),
    [detailReady, setDetailReady] = useState(false);
  const {description, status} = filmDraft;
  const [newTitle, setNewTitle] = useState("");
  const [comments, setComments] = useState(null),
    [commentDrafts, setCommentDrafts] = useState({});
  const selectedRef = useRef(selected);
  selectedRef.current = selected;
  const [liveResults, setLiveResults] = useState({}),
    [batch, setBatch] = useState(null),
    [batchSummary, setBatchSummary] = useState("");
  const [mdbResults, setMdbResults] = useState({}),
    [mdbPending, setMdbPending] = useState(false);
  const batchController = useRef(null);
  async function refresh() {
    setBusy(true);
    setError("");
    try {
      const result = await load(project);
      setFilms(result.films);
      setStates(result.states);
      setDefaultState(result.defaultState);
      try {
        setPreferences((await preferenceRequest("/preferences")).preferences);
      } catch (e) {
        setPreferences(null);
        setError(`Preferences are unavailable: ${e.message}`);
      }
      try {
        setMovary(await preferenceRequest(`/movary/${encodeURIComponent(project)}`));
      } catch {
        setMovary(null);
      }
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  useEffect(() => {
    if (project) refresh();
  }, [project]);
  useEffect(() => {
    const listener = () => setSelected(selectedId());
    window.addEventListener("hashchange", listener);
    return () => window.removeEventListener("hashchange", listener);
  }, []);
  useEffect(() => () => batchController.current?.abort(), []);
  const film = films.find((item) => item.id === selected);
  const preference = preferenceDraft.filmId === film?.id ? preferenceDraft.value : emptyPreference;
  const detailDirty = useRef(false);
  function setPreference(value) {
    setPreferenceDraft({filmId: film.id, value, dirty: true});
  }
  const shownFilms = useMemo(() => films.map((item) => ({
    ...item, live: liveResults[item.id]?.data,
  })), [films, liveResults]);
  const shownFilm = shownFilms.find((item) => item.id === selected);
  const liveMovie = film ? liveResults[film.id]?.data : null;
  const liveError = film ? liveResults[film.id]?.error : null;
  const mdbId = film ? tmdbId(film) : null;
  const mdbResult = mdbId ? mdbResults[mdbId] : null;
  const pending = chooseBatch(films, liveResults);
  const retries = chooseBatch(films, liveResults, true);
  const eligible = films.filter((item) => tmdbId(item)).length;
  const unattempted = films.filter((item) => tmdbId(item) && !liveResults[item.id]).length;
  async function loadMdbRatings() {
    if (!mdbId || mdbPending) return;
    const id = mdbId;
    setMdbPending(true);
    try {
      const ratings = await fetchRatings(id);
      setMdbResults((current) => ({ ...current, [id]: { ratings, error: null } }));
    } catch (error) {
      setMdbResults((current) => ({ ...current, [id]: { ratings: null, error: error.message } }));
    } finally {
      setMdbPending(false);
    }
  }
  const genres = [
    ...new Set(shownFilms.flatMap((item) => [item.fields["POC Genre"], ...(item.live?.genres || [])]).filter(Boolean)),
  ].sort();
  const services = [
    ...new Set(shownFilms.flatMap((item) => providers(item) || [])),
  ].sort();
  useEffect(() => {
    setPreferenceDraft((current) => syncPreferenceDraft(current, film?.id, preferences));
  }, [film?.id, preferences]);
  useEffect(() => { detailDirty.current = false; }, [film?.id]);
  useEffect(() => {
    let active = true;
    setDetailReady(false);
    setComments(null);
    if (film)
      request(`/task/${encodeURIComponent(film.id)}`)
        .then((detail) => {
          if (typeof detail.description !== "string")
            throw new Error(
              "Full synopsis is unavailable; editing is disabled.",
            );
          if (active) {
            setFilmDraft((current) => mergeFilmDraft(current, detail, detailDirty.current));
            setDetailReady(true);
          }
        })
        .catch((e) => {
          if (active) setError(e.message);
        });
    if (film)
      request(`/comment/${encodeURIComponent(film.id)}`)
        .then((rows) => {
          if (active) setComments(rows);
        })
        .catch((e) => {
          if (active) setError(`Comments unavailable: ${e.message}`);
        });
    return () => {
      active = false;
    };
  }, [film]);
  const filtered = useMemo(
    () =>
      filterFilms(shownFilms, {
        query,
        provider,
        watchlistOnly,
        minimum,
        genre,
        lifecycle,
        watched,
        freshnessFilter,
        sortInterest,
        preferences,
        movaryOnly,
        movary,
      }),
    [
      shownFilms,
      query,
      provider,
      watchlistOnly,
      sortInterest,
      preferences,
      movaryOnly,
      movary,
      minimum,
      genre,
      lifecycle,
      watched,
      freshnessFilter,
    ],
  );
  async function savePreference(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const path = encodeURIComponent(film.id);
      const preview = await preferenceRequest(`/preview/${path}`, "POST", {
        preference,
      });
      const watchlistLabel = value => value === null ? "unknown" : value ? "yes" : "no";
      const text = `Preview local preference change:\nInterest: ${preview.before.interest_score ?? "unknown"} → ${preview.after.interest_score ?? "unknown"}\nWatchlist: ${watchlistLabel(preview.before.watchlist)} → ${watchlistLabel(preview.after.watchlist)}\nWatched date: ${preview.before.watched_at || "none recorded"} → ${preview.after.watched_at || "none recorded"}\nNotes before: ${preview.before.personal_notes || "(empty)"}\nNotes after: ${preview.after.personal_notes || "(empty)"}\n\nSave these changes?`;
      if (window.confirm(text)) {
        await preferenceRequest(`/preferences/${path}`, "PUT", {
          preference,
          token: preview.token,
        });
        const updated = (await preferenceRequest("/preferences")).preferences;
        setPreferences(updated);
        setPreferenceDraft((current) => markPreferenceSaved(current, film.id, preference));
      }
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  async function save(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      await request(`/task/description/${encodeURIComponent(film.id)}`, "PUT", {
        description,
      });
      if (status !== film.status)
        await request(`/task/status/${encodeURIComponent(film.id)}`, "PUT", {
          status,
        });
      detailDirty.current = false;
      await refresh();
    } catch (e) {
      setError(`Update may be partial. Reload to check: ${e.message}`);
      setBusy(false);
    }
  }
  async function addFilm(event) {
    event.preventDefault();
    if (!newTitle.trim()) return;
    setBusy(true);
    setError("");
    try {
      const created = await request(
        `/task/${encodeURIComponent(project)}`,
        "POST",
        {
          title: newTitle.trim(),
          description: "",
          priority: "no-priority",
          status: defaultState,
        },
      );
      setNewTitle("");
      await refresh();
      location.hash = `film=${encodeURIComponent(created.id)}`;
    } catch (e) {
      setError(
        `Creation may have failed; reload before retrying: ${e.message}`,
      );
      setBusy(false);
    }
  }
  async function addComment(event) {
    event.preventDefault();
    const target = film.id;
    const draft = commentDrafts[target] || "";
    if (!draft.trim()) return;
    setBusy(true);
    setError("");
    try {
      await request(`/comment/${encodeURIComponent(target)}`, "POST", {
        content: draft.trim(),
      });
      setCommentDrafts((current) => clearSavedDraft(current, target, draft));
      const updated = await request(`/comment/${encodeURIComponent(target)}`);
      setComments((current) => currentComments(selectedRef.current, target, current, updated));
    } catch (e) {
      setError(
        `Comment may have been saved; reload before retrying: ${e.message}`,
      );
    } finally {
      setBusy(false);
    }
  }
  async function startLiveBatch(items) {
    if (!items.length || batchController.current) return;
    const controller = new AbortController();
    batchController.current = controller;
    setBatch({total: items.length, done: 0});
    setBatchSummary("");
    try {
      const result = await runBatch(items, async (id, signal) => {
        const response = await fetch(`http://localhost:15176/movie/${id}`, {
          cache: "no-store", credentials: "include", signal,
        });
        if (!response.ok) throw new Error("Live metadata unavailable");
        const data = await response.json();
        if (!data.availability || !Array.isArray(data.availability.offers)) throw new Error("Invalid metadata response");
        return data;
      }, controller.signal, (id, result, done) => {
        setLiveResults((previous) => ({ ...previous, [id]: mergeResult(previous[id], result) }));
        setBatch({total: items.length, done});
      });
      setBatchSummary(`${result.cancelled ? "Cancelled" : "Finished"}: ${result.succeeded} loaded, ${result.failed} failed. No results were saved to Kaneo.`);
    } finally {
      batchController.current = null;
      setBatch(null);
    }
  }
  function choose(event) {
    event.preventDefault();
    const value = new FormData(event.currentTarget).get("project").trim();
    const next = new URL(location.href);
    next.searchParams.set("project", value);
    next.hash = "";
    location.href = next.href;
  }
  return (
    <>
      <header>
        <a className="brand" href="#">
          FILM <span> / </span> LAB
        </a>
        <nav>
          <a href="#">Discover</a>
          <a href="http://localhost:15173/" target="_blank" rel="noreferrer">
            Kaneo admin ↗
          </a>
        </nav>
        <span className="flag">ISOLATED POC</span>
      </header>
      <main>
        <div className="eyebrow">FILM DISCOVERY / KANEO EXPERIMENT</div>
        <div className="intro">
          <div>
            <h1>
              Stories worth
              <br />
              <em>finding.</em>
            </h1>
            <p>
              A local experimental view of films stored in your Kaneo project.
            </p>
          </div>
          <div className="stats">
            <strong>{films.length}</strong>
            <span>RECORDS LOADED</span>
          </div>
        </div>
        <form className="project" onSubmit={choose}>
          <label>
            Project ID{" "}
            <input
              name="project"
              defaultValue={project}
              required
              placeholder="Kaneo project ID"
            />
          </label>
          <button>Open project</button>
          <a
            href="http://localhost:15173/auth/sign-in"
            target="_blank"
            rel="noreferrer"
          >
            Sign in to Kaneo ↗
          </a>
        </form>
        <p className="notice">
          POC preferences use a separate local store and do not change Movary.
          Movary remains the source of truth for personal watch history.
        </p>
        <p className="notice">{movary?.status === "available" ? `Movary watched snapshot observed ${movary.observed_at}. Missing films remain unknown.` : "Movary watched snapshot unavailable for this user or project."}</p>
        {!!eligible && <section>
          <p>Live metadata is optional and stays only in this open page. Each film can use up to three TMDB requests. {unattempted} of {eligible} supplied IDs have not been attempted. Results are not identity verification. Cancel stops further requests; an in-flight request may finish.</p>
          <button type="button" disabled={!!batch || !pending.length} onClick={() => startLiveBatch(pending)}>Fetch next {pending.length} films (up to {pending.length * 3} requests)</button>{" "}
          {!!retries.length && <button type="button" disabled={!!batch} onClick={() => startLiveBatch(retries)}>Retry up to {BATCH_LIMIT} failed</button>}{" "}
          {batch && <><span role="status">Fetching {batch.done} of {batch.total} films. </span><button type="button" onClick={() => batchController.current?.abort()}>Cancel</button></>}
          {batchSummary && <p role="status">{batchSummary}</p>}
          {Object.values(liveResults).some((result) => result.data) && <Credits />}
        </section>}
        {project && (
          <form className="project" onSubmit={addFilm}>
            <label>
              Add a film to this shared project
              <input
                value={newTitle}
                onChange={(e) => setNewTitle(e.target.value)}
                maxLength="200"
                placeholder="Film title"
                required
              />
            </label>
            <button disabled={busy || !defaultState}>Add film</button>
          </form>
        )}
        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}
        {film ? (
          <section className="detail">
            <a href="#">← Back to discovery</a>
            <div className="detail-grid">
              <div className="poster large">
                {liveMovie?.poster_url ? <img src={liveMovie.poster_url} alt={`TMDB poster for ${liveMovie.title}`} /> : <span>NO POSTER</span>}
              </div>
              <div>
                <div className="eyebrow">
                  {film.fields["POC Genre"] || "GENRE UNKNOWN"} ·{" "}
                  {film.fields["POC Year"] || "YEAR UNKNOWN"}
                </div>
                <h2>{film.title}</h2>
                {movary?.films?.[film.fields["POC TMDB ID"]]?.watched === true && <section>
                  <h3>Watched in Movary</h3>
                  <p>Snapshot observed {movary.observed_at}. Watch dates and counts come from Movary; unknown dates remain unknown.</p>
                  <ul>{(movary.films[film.fields["POC TMDB ID"]].played_watch_dates || []).map((entry, index) => <li key={index}>{entry.date || "Date unknown"} · {entry.plays} play(s)</li>)}</ul>
                  {!!movary.films[film.fields["POC TMDB ID"]].history_export_dates?.length && <p>History export dates: {movary.films[film.fields["POC TMDB ID"]].history_export_dates.map((date) => date || "unknown").join(", ")}. This is a separate source and is not added to play counts.</p>}
                </section>}
                {film.fields["POC TMDB ID"] && (
                  <section>
                    <h3>Live TMDB details</h3>
                    <p>Supplied TMDB ID: {film.fields["POC TMDB ID"]}. Verify that the returned film is the intended work.</p>
                    <button type="button" onClick={() => startLiveBatch([film])} disabled={!!batch || !tmdbId(film)}>
                      Fetch or refresh live details
                    </button>
                    {liveError && <p role="alert">{liveError}</p>}
                    {liveMovie && (
                      <div>
                        <p>TMDB: {liveMovie.title} ({liveMovie.year || "year unknown"})</p>
                        {liveMovie.synopsis && <p>{liveMovie.synopsis}</p>}
                        <p>Genres: {liveMovie.genres?.join(", ") || "Unknown"}. Directors: {liveMovie.directors?.join(", ") || "Unknown"}.</p>
                        <p>US availability: {liveMovie.availability.status}. {liveMovie.availability.offers.map((offer) => `${offer.provider} (${offer.kind})`).join(", ") || (liveMovie.availability.status === "complete" ? "No offers reported" : "Availability unknown")}. Checked: {liveMovie.availability.checked_at}.</p>
                        {liveMovie.availability_attempt && <p>Latest check was {liveMovie.availability_attempt}; showing the earlier complete observation.</p>}
                        {liveMovie.availability.provider_url && <p><a href={liveMovie.availability.provider_url} target="_blank" rel="noreferrer">View provider information on TMDB ↗</a></p>}
                        <p>Fetched on demand; these results are not saved to Kaneo. Provider entitlement is unverified.</p>
                      </div>
                    )}
                  </section>
                )}
                {film.fields["POC Evidence"] && <SourceEvidence film={film} />}
                {mdbId && <section>
                  <h3>Ratings from MDBList</h3>
                  <p>Fetches one result on request. Data stays in this page and is not saved to the tracker.</p>
                  <button type="button" onClick={loadMdbRatings} disabled={mdbPending}>
                    {mdbPending ? "Fetching ratings…" : "Fetch or refresh ratings"}
                  </button>
                  {mdbResult?.error && <p role="alert">{mdbResult.error}</p>}
                  {mdbResult?.ratings && (mdbResult.ratings.length ? <ul>
                    {mdbResult.ratings.map((row, index) => <li key={`${row.source}-${index}`}>
                      {row.source_name} · {row.kind === "unknown" ? "rating type unknown" : row.kind} ·{" "}
                      {row.score_100 === null ? "Score unknown" : `${row.score_100}/100`}
                      {row.votes !== null ? ` · ${row.votes} ratings` : ""}
                      {row.url && <> · <a href={row.url} target="_blank" rel="noreferrer">Source link ↗</a></>}
                    </li>)}
                  </ul> : <p>Ratings unknown; none were returned.</p>)}
                  {mdbResult?.ratings && <p>Source: MDBList. These are reported values; links and scores are not independently verified.</p>}
                </section>}
                <div className="badges">
                  <ProviderBadges film={shownFilm || film} />
                </div>
                <form onSubmit={save}>
                  <label>
                    Synopsis
                    <textarea
                      value={description}
                      onChange={(e) => { detailDirty.current = true; setFilmDraft({...filmDraft, description: e.target.value}); }}
                      rows="7"
                      disabled={!detailReady || busy}
                    />
                  </label>
                  <label>
                    Lifecycle
                    <select
                      value={status}
                      onChange={(e) => { detailDirty.current = true; setFilmDraft({...filmDraft, status: e.target.value}); }}
                      disabled={!detailReady || busy}
                    >
                      {Object.entries(states).map(([value, label]) => (
                        <option key={value} value={value}>
                          {label}
                        </option>
                      ))}
                    </select>
                  </label>
                  <button disabled={busy || !detailReady}>Save to Kaneo</button>
                </form>
                <form onSubmit={savePreference}>
                  <h3>Your local POC preferences</h3>
                  <label>
                    Interest score
                    <select
                      value={preference.interest_score ?? ""}
                      disabled={!preferences}
                      onChange={(e) =>
                        setPreference({
                          ...preference,
                          interest_score: e.target.value
                            ? Number(e.target.value)
                            : null,
                        })
                      }
                    >
                      <option value="">Unknown</option>
                      {Array.from({ length: 10 }, (_, i) => (
                        <option key={i + 1} value={i + 1}>
                          {i + 1}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Watchlist
                      <select
                        value={preference.watchlist === null ? "unknown" : preference.watchlist ? "yes" : "no"}
                        disabled={!preferences}
                        onChange={(e) =>
                          setPreference({
                            ...preference,
                            watchlist: e.target.value === "unknown" ? null : e.target.value === "yes",
                          })
                        }
                      ><option value="unknown">Unknown</option><option value="yes">Yes</option><option value="no">No</option></select>
                  </label>
                  <label>
                    <span>
                      <input
                        type="checkbox"
                        checked={Boolean(preference.watched_at)}
                        disabled={!preferences}
                        onChange={(e) =>
                          setPreference({
                            ...preference,
                            watched_at: e.target.checked
                              ? new Date().toISOString()
                              : null,
                          })
                        }
                      />{" "}
                      Watched timestamp recorded
                    </span>
                  </label>
                  <label>
                    Personal notes
                    <textarea
                      value={preference.personal_notes}
                      disabled={!preferences}
                      onChange={(e) =>
                        setPreference({
                          ...preference,
                          personal_notes: e.target.value,
                        })
                      }
                      rows="3"
                    />
                  </label>
                  <button disabled={busy || !preferences}>
                    Preview and save preferences
                  </button>
                </form>
                <p>
                  Critic score: {film.fields["POC Critic Score"] || "Unknown"}
                </p>
                {film.fields["POC Critic Summary"] && (
                  <p>
                    Synthetic critic summary:{" "}
                    {film.fields["POC Critic Summary"]}
                  </p>
                )}
                {syntheticAvailability(film) && (
                  <p>
                    Synthetic rentals:{" "}
                    {syntheticAvailability(film).rent.join(", ") ||
                      "None reported"}
                    . Checked:{" "}
                    {syntheticAvailability(film).checked_at || "Unknown"}.
                  </p>
                )}
                <section>
                  <h3>Comments</h3>
                  {comments === null ? (
                    <p>Comments unavailable or loading.</p>
                  ) : comments.length ? (
                    comments.map((item) => (
                      <p key={item.id}>
                        <strong>{item.user?.name || "Unknown author"}:</strong>{" "}
                        {item.content}
                      </p>
                    ))
                  ) : (
                    <p>No comments.</p>
                  )}
                  <form onSubmit={addComment}>
                    <label>
                      Add a comment (visible to project members)
                      <textarea
                        value={commentDrafts[film.id] || ""}
                        onChange={(e) => { const text = e.target.value; setCommentDrafts((current) => setCommentDraft(current, film.id, text)); }}
                        rows="3"
                        maxLength="10000"
                        required
                      />
                    </label>
                    <button disabled={busy || comments === null}>
                      Add comment
                    </button>
                  </form>
                </section>
              </div>
            </div>
          </section>
        ) : (
          <section>
            <div className="section-head">
              <div>
                <div className="eyebrow">THE COLLECTION</div>
                <h2>
                  Explore films <small>{filtered.length}</small>
                </h2>
              </div>
              <div className="filters">
                <input
                  aria-label="Search films"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Search titles"
                />
                <select
                  aria-label="Filter by provider"
                  value={provider}
                  onChange={(e) => setProvider(e.target.value)}
                >
                  <option value="">All providers</option>
                  {services.map((p) => (
                    <option key={p}>{p}</option>
                  ))}
                </select>
                <select
                  aria-label="Minimum interest score"
                  value={minimum}
                  disabled={!preferences && !minimum}
                  onChange={(e) => setMinimum(e.target.value)}
                >
                  <option value="">Any interest</option>
                  {Array.from({ length: 10 }, (_, i) => (
                    <option key={i + 1} value={i + 1}>
                      {i + 1} or higher
                    </option>
                  ))}
                </select>
                <select
                  aria-label="Filter by genre"
                  value={genre}
                  onChange={(e) => setGenre(e.target.value)}
                >
                  <option value="">All genres</option>
                  {genres.map((g) => (
                    <option key={g}>{g}</option>
                  ))}
                </select>
                <select
                  aria-label="Filter by lifecycle"
                  value={lifecycle}
                  onChange={(e) => setLifecycle(e.target.value)}
                >
                  <option value="">All states</option>
                  {Object.entries(states).map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </select>
                <select
                  aria-label="Filter by POC watched status"
                  value={watched}
                  disabled={!preferences && !watched}
                  onChange={(e) => setWatched(e.target.value)}
                >
                  <option value="">Any watch status</option>
                  <option value="marked">Marked watched</option>
                  <option value="unmarked">Not marked watched</option>
                </select>
                <select
                  aria-label="Filter by availability freshness"
                  value={freshnessFilter}
                  onChange={(e) => setFreshnessFilter(e.target.value)}
                >
                  <option value="">Any freshness</option>
                  <option value="recent">Checked within 7 days</option>
                  <option value="stale">Older than 7 days</option>
                  <option value="unknown">Unknown freshness</option>
                </select>
                <label>
                  <input
                    type="checkbox"
                    checked={watchlistOnly}
                    disabled={!preferences && !watchlistOnly}
                    onChange={(e) => setWatchlistOnly(e.target.checked)}
                  />{" "}
                  Watchlist
                </label>
                <label>
                  <input type="checkbox" checked={movaryOnly} disabled={movary?.status !== "available" && !movaryOnly} onChange={(e) => setMovaryOnly(e.target.checked)} />{" "}
                  Watched in Movary
                </label>
                <label>
                  <input
                    type="checkbox"
                    checked={sortInterest}
                    disabled={!preferences && !sortInterest}
                    onChange={(e) => setSortInterest(e.target.checked)}
                  />{" "}
                  Sort by interest
                </label>
              </div>
            </div>
            {busy ? (
              <p>Loading records…</p>
            ) : (
              <div className="grid">
                {filtered.map((item) => (
                  <a
                    className="card"
                    key={item.id}
                    href={`#film=${encodeURIComponent(item.id)}`}
                  >
                    <div className="poster">
                      {item.live?.poster_url ? <img src={item.live.poster_url} alt={`TMDB poster for ${item.live.title}`} loading="lazy" /> : <span>NO POSTER</span>}
                      <b>{states[item.status] || item.status}</b>
                    </div>
                    <div className="card-body">
                      <div className="card-meta">
                        {item.fields["POC Genre"] || item.live?.genres?.join(", ") || "UNKNOWN GENRE"} ·{" "}
                        {item.fields["POC Year"] || item.live?.year || "UNKNOWN YEAR"}
                      </div>
                      <h3>{item.title}</h3>
                      {item.live && <p>TMDB match not independently verified</p>}
                      <div className="badges">
                        <ProviderBadges film={item} />
                      </div>
                      <p>
                        Critic score:{" "}
                        {item.fields["POC Critic Score"] || "Unknown"}
                      </p>
                      <p>{movary?.films?.[item.fields["POC TMDB ID"]]?.watched === true ? "Watched in Movary" : "Movary watch status not established"}</p>
                      <p>
                        Interest:{" "}
                        {preferences
                          ? (preferences[item.id]?.interest_score ?? "Unknown")
                          : "Unavailable"}{" "}
                        ·{" "}
                        {preferences
                          ? !preferences[item.id] || preferences[item.id].watchlist === null
                            ? "Watchlist unknown"
                            : preferences[item.id].watchlist
                            ? "Watchlisted"
                            : "Not watchlisted"
                          : "Watchlist unavailable"}
                      </p>
                    </div>
                  </a>
                ))}
              </div>
            )}
          </section>
        )}
      </main>
    </>
  );
}

createRoot(document.getElementById("root")).render(<App />);
