import React, { useEffect, useMemo, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  filterFilms,
  providers,
  syntheticAvailability,
} from "./film_filters.js";
import { ACCESS_DENIED_MESSAGE, AccessDeniedError, BATCH_LIMIT, accessDenied, availabilityTimeLabel, chooseBatch, chooseRemaining, expireCachedResults, fetchCachedMovie, fetchLiveMovie, fetchTaskLiveMovie, hydrateCachedResult, mergeResult, refreshNotice, runBatch, runRemainingBatch, safeImdbTitleUrl, tmdbId } from "./live_batch.js";
import { fetchRatings } from "./mdblist_ui.js";
import { evidenceExplanation, evidenceLabel, sourceEvidenceLinks, sourceLabel } from "./source_evidence.js";
import { clearSavedDraft, currentComments, saveComment, setCommentDraft } from "./comment_drafts.js";
import { emptyPreference, markPreferenceSaved, mergeFilmDraft, syncPreferenceDraft } from "./preference_draft.js";
import { missingLinkedFilm, unavailableFilterSources } from "./availability_state.js";
import { accessibleProjects, projectUrl } from "./project_picker.js";
import { confirmNavigation, guardSameDocumentNavigation, hasCommentDrafts, sameTabClick, selectedFromUrl } from "./navigation_guard.js";
import { readDirectReviews, reviewsMatchTitle, safeReviewUrl } from "./direct_reviews.js";
import { createFilm, CreatedFilmUnverified, identityField, matchedLive } from "./kaneo_identity.js";
import { TmdbCredits } from "./tmdb_credits.jsx";
import { filterMayExcludeUnknown } from "./metadata_filter_coverage.js";
import { metadataChanges, storedMetadata } from "./kaneo_metadata.js";
import { ReviewedCatalog } from "./reviewed_catalog_view.jsx";
import {liveGenreOnlyMatch, storedGenreDisplay, storedGenreLabels} from "./stored_genres.js";
import {Poster} from "./poster.jsx";
import {IdentityReview} from "./identity_review.jsx";
import {ReviewIdentity} from "./review_identity.jsx";
import {ReviewDirectorEvidence} from "./review_director_evidence.jsx";
import {criticScore, CriticFields} from "./critic_fields.jsx";
import {titleNeedsReview} from "./youtrack_tmdb.js";
import {MetadataUnavailable} from "./metadata_status.jsx";

const api = "http://localhost:15173/api";
const cacheFixture = typeof __FILMIQ_CACHE_FIXTURE__ !== "undefined" && __FILMIQ_CACHE_FIXTURE__;
const liveCache = typeof __FILMIQ_LIVE_CACHE__ !== "undefined" && __FILMIQ_LIVE_CACHE__;
const fixtureProject = cacheFixture ? __FILMIQ_FIXTURE_PROJECT__ : "";
const fixtureIds = new Set([900000001, 900000002]);
async function fixtureMovie(item, signal) {
  if (!item || !fixtureIds.has(tmdbId(item))) throw new Error("Fictional ID required");
  const response = await fetch(`http://localhost:15179/cache/${encodeURIComponent(item.id)}`, {credentials: "include", cache: "no-store", signal});
  if (accessDenied(response)) throw new AccessDeniedError();
  if (!response.ok) throw new Error("Fictional cache unavailable");
  return response.json();
}
function ProviderBadges({ film }) {
  const services = providers(film);
  if (services === null) return <span>Availability unknown</span>;
  if (film.live?.availability?.status === "partial" && !services.length)
    return <span>Availability incomplete</span>;
  if (!services.length) return <span>No subscriptions reported</span>;
  return <>{services.map((name) => <span key={name}>{name}</span>)}{film.live?.availability?.status === "partial" && <span>Partial</span>}</>;
}

function SourceEvidence({ film }) {
  let evidence;
  try {
    evidence = JSON.parse(film.fields["POC Evidence"] || "null");
  } catch { evidence = null; }
  const {status, links} = sourceEvidenceLinks(evidence, tmdbId(film));
  return <section>
    <h3>Source evidence</h3>
    {status === "mismatch" && <p role="alert">The supplied TMDB ID differs from the original source evidence. Links are hidden until reviewed; source-listed year and director may refer to the previous ID.</p>}
    {film.fields["POC Identity Provenance"] && <p>Identity provenance: {film.fields["POC Identity Provenance"]}</p>}
    <p>Imported provenance describes the original source assertion. If a title is edited, revalidate it against the saved external identity and tracker history; editing does not update or independently verify provenance.</p>
    {film.fields["POC Source Year"] && <p>Source-listed year: {film.fields["POC Source Year"]} (not independently verified).</p>}
    {film.fields["POC Source Director"] && <p>Source-listed director: {film.fields["POC Source Director"]} (not independently verified).</p>}
    {links.length ? <ul>{links.map((item, index) => {
      let url;
      try { const parsed = new URL(item?.url); if ((parsed.protocol === "https:" || parsed.protocol === "http:") && !parsed.username && !parsed.password) url = parsed.href; } catch { /* Invalid source links stay unavailable. */ }
      return <li key={item?.entry_id || index}>{url ? <a href={url} target="_blank" rel="noreferrer">{sourceLabel(item)} ↗</a> : `${sourceLabel(item)}: link unavailable`} · {evidenceLabel(item?.kind)}{item?.rank ? ` · rank ${item.rank}` : ""}{item?.lineage_kind ? ` · ${item.lineage_kind}` : ""}</li>;
    })}</ul> : <p>Source evidence unknown.</p>}
    <p>{evidenceExplanation(links)}</p>
  </section>;
}

function DirectReviews({ film }) {
  const links = readDirectReviews(film.fields["POC Direct Review Links"], film.fields["POC TMDB ID"]);
  const stale = links?.length && !reviewsMatchTitle(links, film.title);
  return <section><h3>Direct reviews and aggregators</h3>
    {stale ? <p>The film title differs from the reviewed source title; links are hidden until revalidated.</p> : links?.length ? <ul>{links.map((link, index) => {
      const evidence = link.identity_evidence;
      return <li key={index}><a href={safeReviewUrl(link.url)} target="_blank" rel="noreferrer">{link.provider} ↗</a> · {link.type === "individual_critic_review" ? "Individual critic review" : "Review aggregator title page"} · checked {link.checked_at}
        <ReviewIdentity evidence={evidence} />
      </li>;
    })}</ul> : <p>Direct review links unavailable; coverage is unknown.</p>}
    {!!links?.length && <p>Page identity was reviewed against the source record; the TMDB identity was not independently reverified.</p>}
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
  let definitions = null;
  try { definitions = await request(`/custom-field/project/${id}`); } catch { /* Keep the board usable if field definitions cannot be read. */ }
  const values = new Map();
  const taskRows = new Map();
  for (const row of rows) {
    const record = values.get(row.taskId) || {};
    record[row.fieldName] = row.value;
    values.set(row.taskId, record);
    const fields = taskRows.get(row.taskId) || [];
    fields.push(row);
    taskRows.set(row.taskId, fields);
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
    films: films.map((film) => ({ ...film, fields: values.get(film.id) || {}, metadata: storedMetadata(definitions, taskRows.get(film.id) || []) })),
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
    fixtureProject || new URLSearchParams(location.search).get("project") || "",
  );
  const [projectList, setProjectList] = useState(null),
    [projectListError, setProjectListError] = useState(""),
    [chosenProject, setChosenProject] = useState(project);
  const [films, setFilms] = useState([]),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [loaded, setLoaded] = useState(false);
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
    [movaryOnly, setMovaryOnly] = useState(false),
    [excludeMovaryWatched, setExcludeMovaryWatched] = useState(false);
  const [minimum, setMinimum] = useState(""),
    [genre, setGenre] = useState(""),
    [lifecycle, setLifecycle] = useState(""),
    [watched, setWatched] = useState(""),
    [freshnessFilter, setFreshnessFilter] = useState("");
  const [showArchived, setShowArchived] = useState(false);
  const [titleReviewOnly, setTitleReviewOnly] = useState(false);
  const [filmDraft, setFilmDraft] = useState({title: "", description: "", status: "", tmdb: "", year: "", genre: ""}),
    [detailReady, setDetailReady] = useState(false);
  const {title, description, status, tmdb, year, genre: filmGenre} = filmDraft;
  const [newTitle, setNewTitle] = useState("");
  const [newTmdb, setNewTmdb] = useState("");
  const [comments, setComments] = useState(null),
    [commentDrafts, setCommentDrafts] = useState({});
  const selectedRef = useRef(selected);
  selectedRef.current = selected;
  const detailDirty = useRef(false), preferenceDirty = useRef(false), skipHashPrompt = useRef(false);
  const filmFieldsDirty = useRef({title: false, description: false, status: false, tmdb: false});
  const metadataDirty = useRef({year: false, genre: false, genreReset: false});
  preferenceDirty.current = preferenceDraft.dirty && preferenceDraft.filmId === selected;
  const [liveResults, setLiveResults] = useState({}),
    [batch, setBatch] = useState(null),
    [batchSummary, setBatchSummary] = useState("");
  const [cacheGeneration, setCacheGeneration] = useState(0);
  const [mdbResults, setMdbResults] = useState({}),
    [mdbPending, setMdbPending] = useState(false);
  const batchController = useRef(null);
  async function refresh() {
    setBusy(true);
    setError("");
    try {
      const result = await load(project);
      setFilms(cacheFixture ? result.films.filter((item) => fixtureIds.has(tmdbId(item))) : result.films);
      setLoaded(true);
      setStates(result.states);
      setDefaultState(result.defaultState);
      try {
        if (cacheFixture) throw new Error("Preferences disabled in fixture build");
        setPreferences((await preferenceRequest("/preferences")).preferences);
      } catch (e) {
        setPreferences(null);
        setError(`Preferences are unavailable: ${e.message}`);
      }
      try {
        if (cacheFixture) throw new Error("Movary disabled in fixture build");
        setMovary(await preferenceRequest(`/movary/${encodeURIComponent(project)}`));
      } catch {
        setMovary(null);
      }
      return true;
    } catch (e) {
      setLoaded(false);
      setError(e.message);
      return false;
    } finally {
      setBusy(false);
    }
  }
  async function refreshProjects() {
    if (cacheFixture) { setProjectList([{id: fixtureProject, name: "Fictional", workspace: "Fixture"}]); return; }
    setProjectList(null); setProjectListError("");
    try {
      const result = await accessibleProjects(request);
      setProjectList(result.projects);
      if (result.incomplete) setProjectListError("Some workspaces could not be loaded; the project list is incomplete.");
    } catch {
      setProjectList([]);
      setProjectListError("Projects could not be loaded. Sign in to Kaneo and try again.");
    }
  }
  useEffect(() => { refreshProjects(); }, []);
  useEffect(() => {
    if (project) refresh();
  }, [project]);
  useEffect(() => {
    if (!cacheFixture) return;
    let active = true;
    const controller = new AbortController();
    for (const item of films) fixtureMovie(item, controller.signal).then((data) => {
      if (active && data.tmdb_id === tmdbId(item)) setLiveResults((previous) => ({...previous, [item.id]: {data, requestedId: data.tmdb_id}}));
    }).catch(() => {});
    return () => { active = false; controller.abort(); };
  }, [films]);
  useEffect(() => {
    if (!liveCache || cacheFixture) return;
    let active = true;
    const controller = new AbortController();
    void (async () => {
      for (const item of films) {
        const id = tmdbId(item);
        if (!id || !active) continue;
        try {
          const data = await fetchCachedMovie(item, controller.signal);
          if (active) setLiveResults((previous) => hydrateCachedResult(previous, item.id, id, data));
        } catch { /* An absent cache remains unknown and never triggers a live request. */ }
      }
    })();
    return () => { active = false; controller.abort(); };
  }, [films, cacheGeneration]);
  useEffect(() => {
    if (!liveCache || cacheFixture) return;
    const {results, next} = expireCachedResults(liveResults);
    const expireAndReload = () => {
      setLiveResults((current) => expireCachedResults(current).results);
      setCacheGeneration((current) => current + 1);
    };
    if (results !== liveResults) { expireAndReload(); return; }
    if (!Number.isFinite(next)) return;
    const timer = setTimeout(expireAndReload, Math.min(next - Date.now(), 2147483647));
    return () => clearTimeout(timer);
  }, [liveResults]);
  useEffect(() => {
    const confirm = (message) => window.confirm(message);
    const navigate = (event) => {
      if (skipHashPrompt.current) { skipHashPrompt.current = false; return; }
      guardSameDocumentNavigation(event, selectedRef.current, detailDirty.current, preferenceDirty.current, confirm);
    };
    const listener = (event) => {
      const next = selectedId();
      if (!window.navigation && next !== selectedRef.current && !skipHashPrompt.current &&
          !confirmNavigation(detailDirty.current, preferenceDirty.current, confirm)) {
        history.replaceState(history.state, "", event.oldURL);
        return;
      }
      skipHashPrompt.current = false;
      setSelected(next);
    };
    window.navigation?.addEventListener("navigate", navigate);
    window.addEventListener("hashchange", listener);
    return () => { window.navigation?.removeEventListener("navigate", navigate); window.removeEventListener("hashchange", listener); };
  }, []);
  useEffect(() => {
    if (!detailDirty.current && !preferenceDirty.current && !hasCommentDrafts(commentDrafts) && !newTitle.trim() && !newTmdb.trim()) return;
    const listener = (event) => { event.preventDefault(); event.returnValue = ""; };
    window.addEventListener("beforeunload", listener);
    return () => window.removeEventListener("beforeunload", listener);
  });
  useEffect(() => () => batchController.current?.abort(), []);
  const film = films.find((item) => item.id === selected);
  const preference = preferenceDraft.filmId === film?.id ? preferenceDraft.value : emptyPreference;
  function setPreference(value) {
    setPreferenceDraft({filmId: film.id, value, dirty: true});
  }
  const shownFilms = useMemo(() => films.map((item) => ({
    ...item, live: matchedLive(item, liveResults[item.id]),
    titleNeedsReview: titleNeedsReview(tmdbId(item), item.title, liveResults[item.id]?.data),
  })), [films, liveResults]);
  const shownFilm = shownFilms.find((item) => item.id === selected);
  const liveResult = film ? liveResults[film.id]?.data : null;
  const liveMovie = film ? matchedLive(film, liveResults[film.id]) : null;
  const liveError = film ? liveResults[film.id]?.error : null;
  const mdbId = film ? tmdbId(film) : null;
  const mdbResult = mdbId ? mdbResults[mdbId] : null;
  const pending = chooseBatch(films, liveResults);
  const retries = chooseBatch(films, liveResults, true);
  const eligible = films.filter((item) => tmdbId(item)).length;
  const unattempted = films.filter((item) => {
    const id = tmdbId(item), result = liveResults[item.id];
    return id && (!result || (result.requestedId ?? result.data?.tmdb_id) !== id);
  }).length;
  async function loadMdbRatings() {
    if (cacheFixture || !mdbId || mdbPending) return;
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
    ...new Set(shownFilms.flatMap((item) => [...storedGenreLabels(item.fields["POC Genre"]), ...(item.live?.genres || [])]).filter(Boolean)),
  ].sort();
  const services = [
    ...new Set(shownFilms.flatMap((item) => providers(item) || [])),
  ].sort();
  useEffect(() => {
    setPreferenceDraft((current) => syncPreferenceDraft(current, film?.id, preferences));
  }, [film?.id, preferences]);
  useEffect(() => { detailDirty.current = false; filmFieldsDirty.current = {title: false, description: false, status: false, tmdb: false}; metadataDirty.current = {year: false, genre: false, genreReset: false}; }, [film?.id]);
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
            setFilmDraft((current) => mergeFilmDraft(current, {...detail, tmdb: film.fields["POC TMDB ID"] || "", year: film.metadata.year.value, genre: film.metadata.genre.value}, detailDirty.current));
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
  const unavailableSources = unavailableFilterSources({preferences, movary, minimum, watched, watchlistOnly, sortInterest, movaryOnly, excludeMovaryWatched});
  const filtered = useMemo(
    () =>
      filterFilms(shownFilms, {
        query,
        provider,
        watchlistOnly,
        minimum,
        genre,
        lifecycle,
        showArchived,
        titleReviewOnly,
        watched,
        freshnessFilter,
        sortInterest,
        preferences,
        movaryOnly,
        excludeMovaryWatched,
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
      excludeMovaryWatched,
      movary,
      minimum,
      genre,
      lifecycle,
      showArchived,
      titleReviewOnly,
      watched,
      freshnessFilter,
    ],
  );
  const remainingVisible = chooseRemaining(filtered, liveResults);
  const remainingProject = chooseRemaining(films, liveResults);
  const incompleteMetadataFilter = titleReviewOnly || filterMayExcludeUnknown({provider, genre, freshness: freshnessFilter});
  async function savePreference(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    let submitting = false;
    try {
      const path = encodeURIComponent(film.id);
      const preview = await preferenceRequest(`/preview/${path}`, "POST", {
        preference,
      });
      const watchlistLabel = value => value === null ? "unknown" : value ? "yes" : "no";
      const text = `Preview local preference change:\nInterest: ${preview.before.interest_score ?? "unknown"} → ${preview.after.interest_score ?? "unknown"}\nWatchlist: ${watchlistLabel(preview.before.watchlist)} → ${watchlistLabel(preview.after.watchlist)}\nWatched date: ${preview.before.watched_at || "none recorded"} → ${preview.after.watched_at || "none recorded"}\nNotes before: ${preview.before.personal_notes || "(empty)"}\nNotes after: ${preview.after.personal_notes || "(empty)"}\n\nSave these changes?`;
      if (window.confirm(text)) {
        submitting = true;
        const saved = await preferenceRequest(`/preferences/${path}`, "PUT", {
          preference,
          token: preview.token,
        });
        const fields = ["interest_score", "watchlist", "watched_at", "personal_notes"];
        if (!saved?.preference || typeof saved.preference !== "object" || Array.isArray(saved.preference) ||
            Object.keys(saved.preference).length !== fields.length ||
            !fields.every((key) => Object.hasOwn(saved.preference, key) && saved.preference[key] === preview.after[key] && saved.preference[key] === preference[key])) {
          throw new Error("Invalid save response");
        }
        setPreferences((current) => current ? {...current, [film.id]: saved.preference} : current);
        setPreferenceDraft((current) => markPreferenceSaved(current, film.id, preference));
        try {
          const updated = (await preferenceRequest("/preferences")).preferences;
          if (!updated || typeof updated !== "object" || Array.isArray(updated)) throw new Error("Invalid preference list");
          if (!updated[film.id] || fields.some((key) => updated[film.id][key] !== saved.preference[key])) throw new Error("Preference readback differs");
          setPreferences(updated);
        } catch (_) {
          setError("Preferences saved, but the full preference list could not be refreshed. Reload to check the latest values.");
        }
      }
    } catch (e) {
      setError(submitting ? "Preference save could not be confirmed; it may have saved. Reload and check before retrying." : e.message);
    } finally {
      setBusy(false);
    }
  }
  async function save(event) {
    event.preventDefault();
    if (!loaded || !detailReady) { setError("Reload films before saving these edits."); return; }
    if (!title.trim()) { setError("Title cannot be blank."); return; }
    setBusy(true);
    setError("");
    let submitting = false, acknowledged = 0;
    try {
      const metadata = metadataChanges(film.metadata, {year, genre: filmGenre}, metadataDirty.current);
      const identityChanged = filmFieldsDirty.current.tmdb && tmdb !== (film.fields["POC TMDB ID"] || "");
      let fieldId;
      if (identityChanged) {
        if (!tmdb) throw new Error("A saved TMDB ID cannot be cleared here; use tracker administration.");
        fieldId = await identityField(request, project, tmdb, film.id);
      }
      const update = async (path, body) => {
        submitting = true;
        await request(path, "PUT", body);
        acknowledged++;
      };
      if (filmFieldsDirty.current.title && title.trim() !== film.title)
        await update(`/task/title/${encodeURIComponent(film.id)}`, { title: title.trim() });
      if (filmFieldsDirty.current.description)
        await update(`/task/description/${encodeURIComponent(film.id)}`, {description});
      if (filmFieldsDirty.current.status && status !== film.status)
        await update(`/task/status/${encodeURIComponent(film.id)}`, {
          status,
        });
      if (fieldId) await update("/custom-field/value", {taskId: film.id, fieldId, value: tmdb});
      for (const {fieldId: metadataField, value} of metadata)
        await update("/custom-field/value", {taskId: film.id, fieldId: metadataField, value});
      detailDirty.current = false;
      filmFieldsDirty.current = {title: false, description: false, status: false, tmdb: false};
      metadataDirty.current = {year: false, genre: false, genreReset: false};
      if (!await refresh() && acknowledged) setError("Film changes saved, but films could not be reloaded. Reload to confirm the displayed record.");
    } catch (e) {
      if (submitting) setLoaded(false);
      setError(submitting ? `Update may be partial. Reload to check: ${e.message}` : `Could not save: ${e.message}`);
      setBusy(false);
    }
  }
  async function addFilm(event) {
    event.preventDefault();
    if (!newTitle.trim()) return;
    setBusy(true);
    setError("");
    let creating = false;
    try {
      const fieldId = newTmdb ? await identityField(request, project, newTmdb) : null;
      creating = true;
      const created = await createFilm(
        request,
        project,
        {
          title: newTitle.trim(),
          description: "",
          priority: "no-priority",
          status: defaultState,
          ...(fieldId ? {customFields: [{fieldId, value: newTmdb}]} : {}),
        }, fieldId, newTmdb,
      );
      setNewTitle("");
      setNewTmdb("");
      await refresh();
      location.hash = `film=${encodeURIComponent(created.id)}`;
    } catch (e) {
      setError(e instanceof CreatedFilmUnverified ? e.message : creating ? `Creation may be incomplete; reload before retrying: ${e.message}` : `Could not create film: ${e.message}`);
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
      const result = await saveComment(
        () => request(`/comment/${encodeURIComponent(target)}`, "POST", {content: draft.trim()}),
        () => request(`/comment/${encodeURIComponent(target)}`),
        () => setCommentDrafts((current) => clearSavedDraft(current, target, draft)),
      );
      setComments((current) => currentComments(selectedRef.current, target, current, result.comments));
      if (!result.refreshed) setError("Comment saved, but comments could not be reloaded. Reload to see it.");
    } catch (e) {
      setError(
        `Comment may have been saved; reload before retrying: ${e.message}`,
      );
    } finally {
      setBusy(false);
    }
  }
  async function startLiveBatch(items, all = false) {
    if (!items.length || batchController.current) return;
    const controller = new AbortController();
    batchController.current = controller;
    setBatch({total: items.length, done: 0});
    setBatchSummary("");
    try {
      const runner = all ? runRemainingBatch : runBatch;
      const fetcher = cacheFixture ? (id, signal) => fixtureMovie(items.find((item) => tmdbId(item) === id), signal) : liveCache ? (id, signal) => fetchTaskLiveMovie(items.find((item) => tmdbId(item) === id), signal) : fetchLiveMovie;
      const result = await runner(items, fetcher, controller.signal, (id, result, done) => {
        setLiveResults((previous) => ({ ...previous, [id]: mergeResult(previous[id], result) }));
        setBatch({total: items.length, done});
      });
      setBatchSummary(`${result.rateLimited ? "Stopped: TMDB rate limit reached. Wait before retrying failed films or fetching the remainder." : result.accessDenied ? `Stopped: ${ACCESS_DENIED_MESSAGE}` : result.cancelled ? "Cancelled." : all && result.failed ? "Stopped after an unavailable response." : "Finished."} ${result.succeeded} loaded, ${result.failed} failed. No results were saved to Kaneo.`);
    } finally {
      batchController.current = null;
      setBatch(null);
    }
  }
  function mayNavigate() {
    return confirmNavigation(detailDirty.current, preferenceDraft.dirty && preferenceDraft.filmId === selected, (message) => window.confirm(message));
  }
  function guardNavigation(event) {
    if (!sameTabClick(event)) return;
    if (!mayNavigate()) event.preventDefault();
    else if (selectedFromUrl(event.currentTarget.href) !== selectedRef.current) skipHashPrompt.current = true;
  }
  function choose(event) {
    event.preventDefault();
    const value = chosenProject;
    if (!value || value === project) return;
    location.href = projectUrl(location.href, value);
  }
  return (
    <>
      <header>
        <a className="brand" href="#" onClick={guardNavigation}>
          FILM <span> / </span> LAB
        </a>
        <nav>
          <a href="#" onClick={guardNavigation}>Discover</a>
          <a href="http://localhost:15173/" target="_blank" rel="noreferrer">
            Kaneo admin ↗
          </a>
        </nav>
        <span className="flag">ISOLATED POC</span>
      </header>
      <main>
        {cacheFixture && <p role="status"><strong>Offline fictional cache test.</strong> All films, metadata and services shown here are synthetic; this does not exercise live enrichment.</p>}
        <div className="eyebrow">FILM DISCOVERY / KANEO EXPERIMENT</div>
        <div className="intro">
          <div>
            <h1>
              Stories worth <em>finding.</em>
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
            Project{" "}
            <select disabled={cacheFixture} value={chosenProject} onChange={(event) => setChosenProject(event.target.value)}>
              <option value="">{projectList === null ? "Loading projects…" : "Choose an accessible project"}</option>
              {project && !projectList?.some((item) => item.id === project) && <option value={project}>Current project (not in project list)</option>}
              {(projectList || []).map((item) => <option key={item.id} value={item.id}>{item.workspace} / {item.name}</option>)}
            </select>
          </label>
          <button disabled={!chosenProject}>Open project</button>
          <button type="button" onClick={refreshProjects}>Refresh projects</button>
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
        {projectListError && <p role="alert">{projectListError}</p>}
        {projectList && !projectList.length && !projectListError && <p>No accessible active projects found.</p>}
        <p className="notice">{movary?.status === "available" ? `Movary watched snapshot observed ${movary.observed_at}. Missing films remain unknown.` : "Movary watched snapshot unavailable for this user or project."}</p>
        {incompleteMetadataFilter && <p>Active metadata filters can exclude films with unknown metadata, so results may be incomplete. Loading the remaining project films also includes hidden and archived films; failed films require retry, and films without a supplied ID cannot be loaded. Title review only identifies loaded title differences; it does not verify matches.</p>}
        {!!eligible && <section>
          <p>{cacheFixture ? "Fictional cache details can reappear after reload until they expire." : liveCache ? "Cached film details can reappear after reload until they expire, up to seven days." : "Live film details stay available until you close or reload this page."} {unattempted} of {eligible} films have not been loaded yet.</p>
          <button type="button" disabled={!!batch || !pending.length} onClick={() => startLiveBatch(pending)}>Load live details for next {pending.length} films</button>{" "}
          <button type="button" disabled={!!batch || !remainingVisible.length} onClick={() => startLiveBatch(remainingVisible, true)}>Load all {remainingVisible.length} remaining visible films (up to {remainingVisible.length * 3} requests)</button>{" "}
          {incompleteMetadataFilter && <><button type="button" disabled={!!batch || !remainingProject.length} onClick={() => startLiveBatch(remainingProject, true)}>Load all {remainingProject.length} remaining project films, including archived (up to {remainingProject.length * 3} TMDB API requests, plus poster images)</button>{" "}</>}
          {!!retries.length && <button type="button" disabled={!!batch} onClick={() => startLiveBatch(retries)}>Retry up to {BATCH_LIMIT} failed</button>}{" "}
          {batch && <><span role="status">Fetching {batch.done} of {batch.total} films. </span><button type="button" onClick={() => batchController.current?.abort()}>Cancel</button></>}
          {batchSummary && <p role="status">{batchSummary}</p>}
          {!cacheFixture && Object.values(liveResults).some((result) => result.data) && <TmdbCredits />}
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
            <label>Optional supplied TMDB ID<input inputMode="numeric" value={newTmdb} onChange={(e) => setNewTmdb(e.target.value)} placeholder="Positive integer" /></label>
            <button disabled={busy || !defaultState}>Add film</button>
          </form>
        )}
        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}
        {!loaded && project && <button type="button" disabled={busy} onClick={refresh}>Reload films</button>}
        {film ? (
          <section className="detail">
            <a href="#" onClick={guardNavigation}>← Back to discovery</a>
            <div className="detail-grid">
              <div className="poster large">
                <Poster url={liveMovie?.poster_url} alt={`TMDB poster for ${liveMovie?.title}`} transient={liveCache} fallback={<span>NO POSTER</span>} />
              </div>
              <div>
                <div className="eyebrow">
                  {storedGenreDisplay(film.fields["POC Genre"]) ?? "GENRE UNKNOWN"} ·{" "}
                  {film.fields["POC Year"] || "YEAR UNKNOWN"}
                </div>
                <h2>{film.title}</h2>
                <ReviewDirectorEvidence raw={film.fields["POC Direct Review Links"]} filmId={film.fields["POC TMDB ID"]} title={film.title} />
                {liveMovie?.poster_from_previous && <p>Poster from an earlier lookup.</p>}
                {movary?.status === "available" && movary?.films?.[film.fields["POC TMDB ID"]]?.watched === true && <section>
                  <h3>Watched in Movary</h3>
                  <p>Snapshot observed {movary.observed_at}. Watch dates and counts come from Movary; unknown dates remain unknown.</p>
                  <ul>{(movary.films[film.fields["POC TMDB ID"]].played_watch_dates || []).map((entry, index) => <li key={index}>{entry.date || "Date unknown"} · {entry.plays} play(s)</li>)}</ul>
                  {!!movary.films[film.fields["POC TMDB ID"]].history_export_dates?.length && <p>History export dates: {movary.films[film.fields["POC TMDB ID"]].history_export_dates.map((date) => date || "unknown").join(", ")}. This is a separate source and is not added to play counts.</p>}
                </section>}
                {!cacheFixture && <ReviewedCatalog source="kaneo" filmId={film.id} tmdbId={tmdbId(film)} trackerTitle={film.title} />}
                {film.fields["POC TMDB ID"] && (
                  <section>
                    <h3>{cacheFixture ? "Fictional cached details" : "Live TMDB details"}</h3>
                    <p>Supplied TMDB ID: {film.fields["POC TMDB ID"]}. Verify that the returned film is the intended work.</p>
                    <button type="button" onClick={() => startLiveBatch([film])} disabled={!!batch || !tmdbId(film)}>
                      {cacheFixture ? "Read fictional cache" : "Fetch or refresh live details"}
                    </button>
                    {liveError && <p role="alert">{liveError}</p>}
                    {!tmdbId(film) ? <p>A valid supplied TMDB ID is required to load film details.</p> : !liveResult && !liveError && <MetadataUnavailable cached={liveCache || cacheFixture} />}
                    {liveResult && !liveMovie && (liveResult.tmdb_id === tmdbId(film)
                      ? <IdentityReview expectedId={tmdbId(film)} savedTitle={film.title} sourceYear={film.fields["POC Source Year"]} sourceDirector={film.fields["POC Source Director"]} data={liveResult} provider={cacheFixture ? "Fictional cache" : "TMDB"} />
                      : <p role="alert">The saved ID differs from the earlier lookup. Fetch details for the current ID before using its metadata.</p>)}
                    {liveMovie && (
                      <div>
                        <p>{cacheFixture ? "Fictional cache" : "TMDB"}: {liveMovie.title} ({liveMovie.year || "year unknown"})</p>
                        {liveMovie.original_title && <p>TMDB original title: {liveMovie.original_title}</p>}
                        {liveMovie.metadata_attempt && <p>Latest metadata was incomplete; earlier details are shown.</p>}
                        <p>{liveMovie.synopsis || "TMDB synopsis unknown."}</p>
                        <p>Genres: {liveMovie.genres?.join(", ") || "Unknown"}. Directors: {liveMovie.directors?.join(", ") || "Unknown"}.</p>
                        {safeImdbTitleUrl(liveMovie.imdb_title_url) ? <p><a href={safeImdbTitleUrl(liveMovie.imdb_title_url)} target="_blank" rel="noreferrer">IMDb title page ↗</a> · IMDb ID supplied by TMDB; match not independently verified. IMDb ratings are audience ratings.</p> : <p>IMDb title link unknown; TMDB did not supply a usable ID.</p>}
                        <p>US availability: {liveMovie.availability.status}. {liveMovie.availability.offers.map((offer) => `${offer.provider} (${offer.kind})`).join(", ") || (liveMovie.availability.status === "complete" ? "No offers reported" : "Availability unknown")}. {availabilityTimeLabel(liveMovie.availability.status, liveMovie.availability.checked_at)}.</p>
                        {liveMovie.availability_attempt && <p>Latest check was {liveMovie.availability_attempt}; showing the earlier provider observation.</p>}
                        {liveMovie.availability.provider_url && <p><a href={liveMovie.availability.provider_url} target="_blank" rel="noreferrer">View provider information on TMDB ↗</a></p>}
                        <p>{cacheFixture ? "These fictional details come from a local cache and are not saved to Kaneo." : liveCache ? "Film details may come from a local cache for up to seven days; they are not saved to Kaneo. Provider entitlement is unverified." : "Fetched on demand; these results are not saved to Kaneo. Provider entitlement is unverified."}</p>
                      </div>
                    )}
                  </section>
                )}
                {(film.fields["POC Evidence"] || film.fields["POC Source Director"] || film.fields["POC Source Year"] || film.fields["POC Identity Provenance"]) && <SourceEvidence film={film} />}
                <DirectReviews film={film} />
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
                    Title
                    <input value={title} onChange={(e) => { detailDirty.current = true; filmFieldsDirty.current.title = true; setFilmDraft({...filmDraft, title: e.target.value}); }} maxLength="200" required disabled={!detailReady || busy} readOnly={!loaded} />
                  </label>
                  <label>Supplied TMDB ID (not independently verified)<input inputMode="numeric" value={tmdb} onChange={(e) => {detailDirty.current = true; filmFieldsDirty.current.tmdb = true; setFilmDraft({...filmDraft, tmdb: e.target.value});}} disabled={!detailReady || busy} readOnly={!loaded} /></label>
                  <p>Changing this ID does not verify the match. Live lookup is optional and uses your authenticated Kaneo session.</p>
                  <label>Stored release year<input inputMode="numeric" value={year} onChange={(e) => {detailDirty.current = true; metadataDirty.current.year = true; setFilmDraft({...filmDraft, year: e.target.value});}} disabled={!detailReady || busy} readOnly={!loaded || !film.metadata.year.editable} /></label>
                  <label>Stored genres (one per line)<textarea value={filmGenre} onChange={(e) => {detailDirty.current = true; metadataDirty.current.genre = true; metadataDirty.current.genreReset = false; setFilmDraft({...filmDraft, genre: e.target.value});}} disabled={!detailReady || busy} readOnly={!loaded || !film.metadata.genre.editable} /></label>
                  {film.metadata.genre.status === "known" && film.metadata.genre.value === "" && filmGenre === "" && <p>No stored genres. <button type="button" disabled={!loaded || !detailReady || busy || !film.metadata.genre.editable} onClick={() => {detailDirty.current = true; metadataDirty.current.genre = true; metadataDirty.current.genreReset = true; setFilmDraft({...filmDraft, genre: ""});}}>Set genres to unknown</button>{metadataDirty.current.genreReset && " Will reset when saved."}</p>}
                  {(!film.metadata.year.editable || !film.metadata.genre.editable) && <p>Release year or genre cannot be edited because its project field is unavailable or invalid.</p>}
                  <p>Stored year and genre are editable fields; clearing either leaves it unknown and does not change source-listed assertions.</p>
                  <label>
                    Synopsis
                    <textarea
                      value={description}
                      onChange={(e) => { detailDirty.current = true; filmFieldsDirty.current.description = true; setFilmDraft({...filmDraft, description: e.target.value}); }}
                      rows="7"
                      disabled={!detailReady || busy}
                      readOnly={!loaded}
                    />
                  </label>
                  <label>
                    Lifecycle
                    <select
                      value={status}
                      onChange={(e) => { detailDirty.current = true; filmFieldsDirty.current.status = true; setFilmDraft({...filmDraft, status: e.target.value}); }}
                      disabled={!loaded || !detailReady || busy}
                    >
                      {Object.entries(states).map(([value, label]) => (
                        <option key={value} value={value}>
                          {label}
                        </option>
                      ))}
                    </select>
                  </label>
                  <button disabled={busy || !loaded || !detailReady}>Save to Kaneo</button>
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
                <CriticFields score={film.fields["POC Critic Score"]} summary={film.fields["POC Critic Summary"]} />
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
                  Explore films <small>{unavailableSources.length ? "—" : filtered.length}</small>
                </h2>
              </div>
              <div className="filters">
                <input
                  aria-label="Search films"
                  aria-description="Search by title or director"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Search title or director"
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
                  <option value="">{showArchived ? "All states" : "Active states"}</option>
                  {Object.entries(states).map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </select>
                <label><input type="checkbox" checked={showArchived} onChange={(e) => setShowArchived(e.target.checked)} /> Show archived</label>
                <label><input type="checkbox" checked={titleReviewOnly} onChange={(e) => setTitleReviewOnly(e.target.checked)} /> Title differences to review</label>
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
                  <input type="checkbox" checked={movaryOnly} disabled={movary?.status !== "available" && !movaryOnly} onChange={(e) => {setMovaryOnly(e.target.checked); if (e.target.checked) setExcludeMovaryWatched(false);}} />{" "}
                  Watched in Movary
                </label>
                <label>
                  <input type="checkbox" checked={excludeMovaryWatched} disabled={movary?.status !== "available" && !excludeMovaryWatched} onChange={(e) => {setExcludeMovaryWatched(e.target.checked); if (e.target.checked) setMovaryOnly(false);}} />{" "}
                  Exclude known watched in Movary
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
            {query && <p>Director search uses source-listed, review identity evidence or loaded live metadata; films with unknown directors may be missing.</p>}
            {missingLinkedFilm(selected, film, loaded, busy) && <p role="alert">The linked film is unavailable in this project. It may have been removed or you may not have access. <a href="#">Clear film link</a></p>}
            {busy ? (
              <p>Loading records…</p>
            ) : unavailableSources.length ? (
              <p role="alert">Cannot apply filters: {unavailableSources.join(" and ")} unavailable. <button type="button" onClick={() => {setMinimum(""); setWatched(""); setWatchlistOnly(false); setSortInterest(false); setMovaryOnly(false); setExcludeMovaryWatched(false);}}>Clear personal filters</button></p>
            ) : (
              <div className="grid">
                {filtered.map((item) => (
                  <a
                    className="card"
                    key={item.id}
                    href={`#film=${encodeURIComponent(item.id)}`}
                  >
                    <div className="poster">
                      <Poster url={item.live?.poster_url} alt={`TMDB poster for ${item.live?.title}`} loading="lazy" transient={liveCache} fallback={<span>NO POSTER</span>} />
                      <b>{states[item.status] || item.status}</b>
                    </div>
                    <div className="card-body">
                      <div className="card-meta">
                        {storedGenreDisplay(item.fields["POC Genre"]) ?? (item.live?.genres?.join(", ") || "UNKNOWN GENRE")} ·{" "}
                        {item.fields["POC Year"] || item.live?.year || "UNKNOWN YEAR"}
                      </div>
                      {liveGenreOnlyMatch(item.fields["POC Genre"], item.live?.genres, genre) && <p>{cacheFixture ? "Fictional cache" : "TMDB"} genre match: {genre}</p>}
                      <h3>{item.title}</h3>
                      {query && <ReviewDirectorEvidence raw={item.fields["POC Direct Review Links"]} filmId={item.fields["POC TMDB ID"]} title={item.title} query={query} />}
                      {item.titleNeedsReview && <p>Title differs from TMDB; open to review.</p>}
                      {item.live && <p>TMDB match not independently verified</p>}
                      {item.live?.poster_from_previous && <p>Poster from an earlier lookup.</p>}
                      <div className="badges">
                        <ProviderBadges film={item} />
                      </div>
                      {refreshNotice(liveResults[item.id], tmdbId(item), item.live) && <p>{refreshNotice(liveResults[item.id], tmdbId(item), item.live)}</p>}
                      <p>
                        Critic score (source not recorded):{" "}
                        {criticScore(item.fields["POC Critic Score"])}
                      </p>
                      <p>{movary?.status === "available" && movary?.films?.[item.fields["POC TMDB ID"]]?.watched === true ? "Watched in Movary" : "Movary watch status not established"}</p>
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
