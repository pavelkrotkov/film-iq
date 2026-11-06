import React, { useEffect, useMemo, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import { readDirectReviews, reviewsMatchTitle, safeReviewUrl } from "./direct_reviews.js";
import { field, filmYearLabel, filterYoutrackFilms, localWatchLabel, localWatchlistLabel, providerObservation, providerFreshness } from "./youtrack_filters.js";
import { boundedRead, loadFilmView, publishFilmBatch } from "./youtrack_loading.js";
import { attachMatchedLive, eligibleLiveFilms, failedLiveFilms, liveMetadataMatches, LiveRateLimited, mergeLiveResult, readLiveMetadata, remainingLiveFilms, runLiveBatch, runRemainingLive, suppliedTmdbId } from "./youtrack_tmdb.js";
import { filmBaseline, filmChanges, hasDuplicateTmdbId, parseOptionalTmdbId } from "./youtrack_edit.js";
import { handleExternalRoute, hasUnsavedPageDraft, routeLocation } from "./youtrack_navigation.js";
import { TmdbCredits } from "./tmdb_credits.jsx";
import { filterMayExcludeUnknown } from "./metadata_filter_coverage.js";
import { movaryHistory } from "./movary_history.js";
import { ReviewedCatalog } from "./reviewed_catalog_view.jsx";
import {storedGenreDisplay, storedGenreLabels} from "./stored_genres.js";
import {availabilityTimeLabel, expireCachedResults, hydrateCachedResult, refreshNotice} from "./live_batch.js";
import {Poster} from "./poster.jsx";
import {IdentityReview} from "./identity_review.jsx";
import {ReviewIdentity} from "./review_identity.jsx";
import {criticScore, CriticFields} from "./critic_fields.jsx";
import {clearSavedDraft, currentComments, saveComment} from "./comment_drafts.js";
import {MetadataUnavailable} from "./metadata_status.jsx";
import {sourceEvidenceLinks} from "./source_evidence.js";
export { providerObservation, providerFreshness } from "./youtrack_filters.js";

let locationListener = () => {};
const host = await YTApp.register({ onAppLocationChange: (location) => locationListener(location) });
const cacheFixture = typeof __FILMIQ_CACHE_FIXTURE__ !== "undefined" && __FILMIQ_CACHE_FIXTURE__;
const liveCache = typeof __FILMIQ_LIVE_CACHE__ !== "undefined" && __FILMIQ_LIVE_CACHE__;
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
// The YouTrack full-page widget iframe lacks allow-forms, so native submit is blocked.
export function submitOnEnter(event, action) {
  if (event.key !== "Enter" || event.shiftKey || event.nativeEvent?.isComposing || event.target?.tagName !== "INPUT") return;
  event.preventDefault();
  action(event);
}
export function providerDescription(observation, key) {
  if (!observation || observation.status === "unknown" || !observation[key]) return "Unknown";
  if (!observation[key].length) return observation.status === "complete" ? "None reported" : "Unknown (partial response)";
  return observation[key].join(", ") + (observation.status === "partial" ? " (partial)" : "");
}

export function parseAppLocation(where) {
  const params = new URLSearchParams(where?.search || "");
  const requested = params.get("project");
  const project = cacheFixture ? "FILMPOC" : ["FILMPOC", "FILMREAL"].includes(requested) ? requested : "FILMREAL";
  const id = params.get("film");
  return {project, film: id && new RegExp(`^${project}-[1-9]\\d*$`).test(id) ? id : null};
}
export async function readPreferences() {
  // YouTrack 2026.2.19728 throws in its host bridge if options are omitted.
  const response = await host.fetchApp("preferences/all", {});
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
function DraftExitWarning({kind}) {
  return <p className="notice" role="status">Unsaved {kind} will be lost if you reload the browser or leave YouTrack. Save or copy them first.</p>;
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
  const [showArchived, setShowArchived] = useState(false);
  const [titleReviewOnly, setTitleReviewOnly] = useState(false);
  const [watchlistOnly, setWatchlistOnly] = useState(false), [sortInterest, setSortInterest] = useState(false);
  const [localWatched, setLocalWatched] = useState("");
  const [provider, setProvider] = useState(""), [genre, setGenre] = useState(""), [freshness, setFreshness] = useState("");
  const [title, setTitle] = useState(""), [synopsis, setSynopsis] = useState(""), [state, setState] = useState(""), [pref, setPref] = useState(emptyPreference);
  const [releaseYear, setReleaseYear] = useState(""), [filmGenre, setFilmGenre] = useState("");
  const [genreReset, setGenreReset] = useState(false);
  const [tmdbId, setTmdbId] = useState(""), [editBaseline, setEditBaseline] = useState(null), [newTmdbId, setNewTmdbId] = useState("");
  const [prefDirty, setPrefDirty] = useState(false), [filmDirty, setFilmDirty] = useState(false);
  const [pendingPreview, setPendingPreview] = useState(null), [pendingNavigation, setPendingNavigation] = useState(null), [discardFailed, setDiscardFailed] = useState(false), [saveUncertain, setSaveUncertain] = useState(false);
  const [restoringLocation, setRestoringLocation] = useState(false);
  const [comments, setComments] = useState(null), [commentDrafts, setCommentDrafts] = useState({}), [newTitle, setNewTitle] = useState("");
  const [createUncertain, setCreateUncertain] = useState(false);
  const [liveResults, setLiveResults] = useState({}), [liveBusy, setLiveBusy] = useState(false), [liveRateLimited, setLiveRateLimited] = useState(false);
  const [cacheGeneration, setCacheGeneration] = useState(0);
  const [liveBatch, setLiveBatch] = useState(null), [liveSummary, setLiveSummary] = useState("");
  const liveRequest = useRef(false), liveCancel = useRef(false);
  const sequence = useRef(0), selectedRef = useRef(selected), projectRef = useRef(project), restoringCount = useRef(0), guardsRef = useRef({});
  selectedRef.current = selected;
  projectRef.current = project;
  guardsRef.current = {filmDirty, prefDirty, pendingPreview, pendingNavigation, busy};
  function setWorking(value) { guardsRef.current.busy = value; setBusy(value); }
  function markFilmDirty(value) { guardsRef.current.filmDirty = value; setFilmDirty(value); }
  function markPrefDirty(value) { guardsRef.current.prefDirty = value; setPrefDirty(value); }
  function setPreview(value) { guardsRef.current.pendingPreview = value; setPendingPreview(value); }
  function setQueued(value) { guardsRef.current.pendingNavigation = value; setPendingNavigation(value); }

  async function refresh(target = project) {
    if (!target || target !== projectRef.current) return;
    const run = ++sequence.current;
    setLoadingFilms(true); setPreferences(null); setMovary(null); setError(""); setNotice("");
    try {
      const [personal, watched] = await loadFilmView({
        loadFilms: async () => {
          const loaded = await getFilms(target);
          return cacheFixture ? loaded.filter((item) => [900000001, 900000002].includes(suppliedTmdbId(item))) : loaded;
        },
        loadPreferences: cacheFixture ? () => Promise.reject(new Error("Disabled in fixture build")) : readPreferences,
        loadWatched: cacheFixture ? () => Promise.reject(new Error("Disabled in fixture build")) : () => host.fetchApp("movary/watched", { query: { project: target } }),
        publishFilms: (loaded) => publishFilmBatch(run, sequence, loaded, setFilms, setLoadingFilms),
      });
      if (run !== sequence.current) return;
      setPreferences(personal.status === "fulfilled" ? personal.value : null);
      setMovary(watched.status === "fulfilled" ? watched.value : null);
      const messages = [];
      if (personal.status === "rejected") {
        setMinimum(""); setWatchlistOnly(false); setSortInterest(false); setLocalWatched("");
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
    setFilms([]); setPreferences(null); setMovary(null); setLiveResults({}); setLiveSummary("");
    refresh(project);
    return () => { sequence.current++; };
  }, [project]);
  useEffect(() => {
    if (!cacheFixture || liveCache) return;
    let active = true;
    for (const item of films) readLiveMetadata(host, item).then((data) => {
      if (active) setLiveResults((previous) => ({...previous, [item.idReadable]: {data, requestedId: data.tmdb_id}}));
    }).catch(() => {});
    return () => { active = false; };
  }, [films]);
  useEffect(() => {
    if (!liveCache) return;
    let active = true;
    void (async () => {
      for (const item of films) {
        if (!suppliedTmdbId(item) || !active) continue;
        try {
          const data = await readLiveMetadata(host, item, {cacheOnly:true});
          if (active) setLiveResults((previous) => hydrateCachedResult(previous, item.idReadable, suppliedTmdbId(item), data));
        } catch { /* Cache misses remain unknown and never cause provider requests. */ }
      }
    })();
    return () => { active = false; };
  }, [films, cacheGeneration]);
  useEffect(() => {
    if (!liveCache) return;
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
    let active = true;
    let navigated = false;
    const apply = (next) => {
      if (!active) return;
      projectRef.current = next.project; selectedRef.current = next.film;
      setProject(next.project); setSelected(next.film);
    };
    locationListener = (where) => {
      navigated = true;
      void handleExternalRoute(
        {project: projectRef.current, film: selectedRef.current}, parseAppLocation(where), guardsRef.current,
        {
          apply,
          queue: (next) => setQueued({kind: "route", value: next}),
          restore: async (current) => {
            restoringCount.current++; setRestoringLocation(true);
            try { await host.navigation.replaceAppLocation(routeLocation(current)); }
            finally { restoringCount.current--; if (!restoringCount.current && active) setRestoringLocation(false); }
          },
          notify: (message) => { if (active) setError(message); },
        },
      );
    };
    host.navigation.getAppLocation().then((where) => { if (!navigated) apply(parseAppLocation(where)); }).catch(() => { if (!navigated) apply(parseAppLocation({search: ""})); });
    return () => { active = false; locationListener = () => {}; };
  }, []);
  const film = films.find((item) => item.idReadable === selected);
  useEffect(() => {
    if (!film) return;
    let active = true;
    markPrefDirty(false); markFilmDirty(false);
    setComments(null);
    getComments(film).then((items) => { if (active) setComments(items); }).catch(() => { if (active) setComments(null); });
    return () => { active = false; };
  }, [film?.idReadable]);
  useEffect(() => {
    if (film && !filmDirty) {
      const baseline = filmBaseline(film);
      setTitle(baseline.title);
      setSynopsis(baseline.synopsis);
      setState(baseline.state);
      setTmdbId(baseline.tmdbId == null ? "" : String(baseline.tmdbId));
      setReleaseYear(baseline.releaseYear == null ? "" : String(baseline.releaseYear));
      setFilmGenre(baseline.genre ?? "");
      setGenreReset(false);
      setEditBaseline(baseline);
    }
  }, [film, filmDirty]);
  useEffect(() => {
    if (film && !prefDirty) setPref(preferences?.[film.idReadable] || emptyPreference);
  }, [film?.idReadable, preferences, prefDirty]);
  async function navigateRoute(next) {
    markFilmDirty(false); markPrefDirty(false);
    projectRef.current = next.project; selectedRef.current = next.film;
    setProject(next.project); setSelected(next.film);
    try { await host.navigation.updateAppLocation(routeLocation(next)); }
    catch { setError("Navigation could not be saved; the current screen may not survive reload."); }
  }
  async function selectFilm(id, discard = false) {
    if (pendingPreview || (pendingNavigation && !discard)) return;
    if ((filmDirty || prefDirty) && !discard) { setQueued({kind: "film", value: id}); return; }
    await navigateRoute({project: projectRef.current, film: id});
  }
  async function selectProject(next, discard = false) {
    if (pendingPreview || (pendingNavigation && !discard)) return;
    if ((filmDirty || prefDirty) && !discard) { setQueued({kind: "project", value: next}); return; }
    await navigateRoute({project: next, film: null});
  }
  const shownFilms = useMemo(() => attachMatchedLive(films, liveResults), [films, liveResults]);
  const providers = [...new Set(shownFilms.flatMap((item) => {
    const observation = providerObservation(item);
    return observation?.status !== "unknown" ? observation?.subscription || [] : [];
  }))].sort();
  const genres = [...new Set(shownFilms.flatMap((item) => [...storedGenreLabels(field(item, "FilmIQ Genre")), ...(item.live?.genres || [])]).filter((value) => typeof value === "string" && value))].sort();
  const visible = useMemo(() => filterYoutrackFilms(shownFilms, {preferences, query, stateFilter, minimum, watchlistOnly, sortInterest, movaryOnly, excludeMovaryWatched, movary, provider, genre, freshness, localWatched, showArchived, titleReviewOnly}), [shownFilms, preferences, query, stateFilter, minimum, watchlistOnly, sortInterest, movaryOnly, excludeMovaryWatched, movary, provider, genre, freshness, localWatched, showArchived, titleReviewOnly]);
  const remainingVisible = remainingLiveFilms(visible, liveResults);
  const remainingProject = remainingLiveFilms(films, liveResults);
  const incompleteMetadataFilter = titleReviewOnly || filterMayExcludeUnknown({provider, genre, freshness});
  const failedFilms = failedLiveFilms(films, liveResults);
  async function saveFilm(event) {
    event.preventDefault(); if (!film || editBaseline?.issueId !== film.id) return; setWorking(true); setError("");
    let submitting = false;
    try {
      const {changes, tmdbId: proposedId, idChanged} = filmChanges(editBaseline, {title, synopsis, state, tmdbId, releaseYear, genre: filmGenre, genreReset});
      if (!Object.keys(changes).length) { markFilmDirty(false); setNotice("No film changes to save."); return; }
      if (idChanged && proposedId && hasDuplicateTmdbId(await getFilms(project), proposedId, film.id)) throw new Error("That TMDB ID is already used by another visible film in this project.");
      submitting = true;
      await host.fetchYouTrack(`issues/${encodeURIComponent(film.id)}`, { method: "POST", body: changes });
      submitting = false;
      const refreshed = await refresh();
      if (refreshed) { markFilmDirty(false); setNotice("Film changes saved in YouTrack."); }
      else setError("Film changes saved, but refresh failed. Reload to confirm the displayed record.");
    } catch (e) { setError(submitting ? "Save may have completed. Reload before retrying." : `Could not save film: ${e.message}`); }
    finally { setWorking(false); }
  }
  async function savePreference(event) {
    event.preventDefault(); if (preferences === null || !film) return; setWorking(true); setError(""); const target = film.idReadable;
    try {
      const preview = await host.fetchApp("preferences/preview", { method: "POST", body: { issue_id: target, preference: pref } });
      if (!previewMatchesFilm(preview, target)) throw new Error("Invalid preview");
      setDiscardFailed(false); setSaveUncertain(false);
      if (selectedRef.current !== target) {
        try {
          await host.fetchApp("preferences/discard", { method: "POST", body: preview });
          setNotice("The selected film changed; the earlier preference preview was discarded.");
        } catch {
          setPreview(preview); setDiscardFailed(true);
          setError("The selected film changed and the earlier preview could not be cleared.");
        }
        return;
      }
      setPreview(preview);
    } catch (e) { setError(`Could not prepare preference preview: ${e.message}`); }
    finally { setWorking(false); }
  }
  async function confirmPreference() {
    if (!previewMatchesFilm(pendingPreview, selectedRef.current)) { setError("The selected film changed; cancel and preview again."); return; }
    setWorking(true); setError(""); let saved = false; const target = pendingPreview.issue_id;
    try {
      await host.fetchApp("preferences/confirm", { method: "POST", body: pendingPreview });
      saved = true;
      setPreview(null); setDiscardFailed(false); setSaveUncertain(false);
      setPreferences(await readPreferences());
      if (selectedRef.current === target) markPrefDirty(false);
      setNotice(`Local preference for ${target} saved; Movary was not changed.`);
    } catch (e) {
      if (saved) setError(`Preference saved, but refresh failed: ${e.message}`);
      else { setSaveUncertain(true); setDiscardFailed(true); setError("Save may have completed. Close this preview, then open a new preview to compare the server's Before value."); }
    }
    finally { setWorking(false); }
  }
  async function discardPreference() {
    setWorking(true); setError("");
    try {
      await host.fetchApp("preferences/discard", { method: "POST", body: pendingPreview });
      setPreview(null); setDiscardFailed(false);
      setNotice(saveUncertain ? "Preview closed; open a new preview to compare the server's Before value." : "Preference preview discarded; no preference was saved.");
      setSaveUncertain(false);
    } catch { setDiscardFailed(true); setError("Cancellation could not clear the server preview; retry or close it locally."); }
    finally { setWorking(false); }
  }
  async function addComment(event) {
    event.preventDefault();
    const target = film, text = commentDrafts[target.idReadable] || "";
    if (!text.trim()) return;
    setWorking(true); setError("");
    try {
      const result = await saveComment(
        () => host.fetchYouTrack(`issues/${encodeURIComponent(target.id)}/comments`, { method: "POST", body: { text } }),
        () => getComments(target),
        () => setCommentDrafts((drafts) => clearSavedDraft(drafts, target.idReadable, text)),
      );
      setComments((current) => currentComments(selectedRef.current, target.idReadable, current, result.comments));
      if (!result.refreshed) setError("Comment saved, but comments could not be reloaded. Reload to see it.");
    } catch (e) { setError(`Comment may have been saved; check before retrying: ${e.message}`); }
    finally { setWorking(false); }
  }
  async function addFilm(event) {
    event.preventDefault(); if (!newTitle.trim() || createUncertain) return;
    setWorking(true); setError(""); setNotice("Checking the project before creating the film…");
    let submitting = false;
    try {
      const id = parseOptionalTmdbId(newTmdbId);
      if (id && hasDuplicateTmdbId(await getFilms(project), id)) throw new Error("That TMDB ID is already used by another visible film in this project.");
      const projectInfo = await boundedRead(() => host.fetchYouTrack(`admin/projects/${project}`, { query: { fields: "id" } }), 15000, "Project lookup timed out");
      const body = { project: { id: projectInfo.id }, summary: newTitle.trim() };
      if (id) body.customFields = [{name: "FilmIQ TMDB ID", $type: "SimpleIssueCustomField", value: id}];
      submitting = true;
      setNotice("Creating the film. YouTrack may ask you to confirm the request…");
      const created = await boundedRead(() => host.fetchYouTrack("issues", { method: "POST", query: { fields: "idReadable" }, body }), 30000);
      if (typeof created?.idReadable !== "string") throw new Error("Creation response was incomplete");
      submitting = false;
      setNewTitle(""); setNewTmdbId("");
      if (await refresh()) await selectFilm(created.idReadable);
      else setError("Film created, but refresh failed. Reload to confirm the displayed record.");
    } catch (e) { if (submitting) setCreateUncertain(true); setNotice(""); setError(submitting ? "Creation may have completed. Reload this page and search for the film before retrying." : `Could not create film: ${e.message}`); }
    finally { setWorking(false); }
  }
  async function loadLiveMetadata() {
    if (!film || !suppliedTmdbId(film) || liveRequest.current || liveRateLimited) return;
    const target = film, targetProject = project;
    liveRequest.current = true; setLiveBusy(true);
    try {
      const data = await readLiveMetadata(host, target);
      if (projectRef.current === targetProject) setLiveResults((previous) => ({...previous, [target.idReadable]: mergeLiveResult(previous[target.idReadable], {data, requestedId: suppliedTmdbId(target)})}));
    } catch (error) {
      const limited = error instanceof LiveRateLimited;
      if (limited) setLiveRateLimited(true);
      if (projectRef.current === targetProject) setLiveResults((previous) => ({...previous, [target.idReadable]: mergeLiveResult(previous[target.idReadable], {requestedId: suppliedTmdbId(target), error: limited ? "TMDB rate limit reached. Wait and reload the page before trying again." : "Live metadata is unavailable. No automatic retry was made."})}));
    } finally { liveRequest.current = false; setLiveBusy(false); }
  }
  async function loadNextLiveBatch(all = false, retry = false, entireProject = false) {
    const items = retry ? failedFilms : entireProject ? remainingProject : all ? remainingVisible : eligibleLiveFilms(visible, liveResults);
    if (!items.length || liveRequest.current || liveRateLimited) return;
    const targetProject = project, run = sequence.current;
    const sameContext = () => projectRef.current === targetProject && sequence.current === run;
    const active = () => sameContext() && !liveCancel.current;
    let done = 0;
    liveCancel.current = false; liveRequest.current = true; setLiveBusy(true); setLiveBatch({done: 0, total: items.length}); setLiveSummary("");
    try {
      const runner = all || retry ? runRemainingLive : runLiveBatch;
      const result = await runner(host, items, active, (item, outcome) => {
        setLiveResults((previous) => ({...previous, [item.idReadable]: mergeLiveResult(previous[item.idReadable], outcome)}));
        setLiveBatch({done: ++done, total: items.length});
      });
      if (sameContext() && result.rateLimited) setLiveRateLimited(true);
      if (sameContext()) setLiveSummary(`${result.rateLimited ? "Stopped after a rate limit. Wait and reload before trying again." : result.cancelled ? "Stopped." : result.failed ? "Stopped after an unavailable response." : "Finished."} ${result.succeeded} loaded; ${result.failed} unavailable. No automatic retries or tracker writes.`);
    } finally { liveRequest.current = false; setLiveBusy(false); setLiveBatch(null); }
  }
  function changePreference(values) { setPref((current) => ({...current, ...values})); markPrefDirty(true); }
  const evidence = film ? sourceEvidence(film) : {};
  const sourceEvidenceState = sourceEvidenceLinks(evidence, suppliedTmdbId(film));
  const sourceLinks = sourceEvidenceState.links;
  const reviews = film ? directReviews(film) : null;
  const staleReviews = film && reviews?.length && !reviewsMatchTitle(reviews, film.summary);
  const savedLiveEntry = film ? liveResults[film.idReadable] : null;
  const liveEntry = savedLiveEntry && (savedLiveEntry.requestedId ?? savedLiveEntry.data?.tmdb_id) === suppliedTmdbId(film) ? savedLiveEntry : null;
  const live = liveEntry?.data?.tmdb_id === suppliedTmdbId(film) ? liveEntry.data : null;
  const liveMatches = liveMetadataMatches(film, live);
  const observation = film ? providerObservation(liveMatches ? {...film, live} : film) : null;
  const watchedHistory = film ? movaryHistory(movary, film.idReadable) : null;
  const locked = busy || loadingFilms || restoringLocation || !!pendingPreview || !!pendingNavigation;
  const filmEditLocked = locked || editBaseline?.issueId !== film?.id;
  const hasPageDraft = hasUnsavedPageDraft({filmDirty, prefDirty, commentDrafts, newTitle, newTmdbId});
  const preferenceLabel = (value) => value === null ? "unknown" : value === true ? "yes" : value === false ? "no" : value;
  return <>
    <header><button className="brand" type="button" disabled={locked} onClick={() => selectFilm(null)} style={{background:"transparent",color:"inherit",padding:0}}>FILM <span> / </span> LAB</button><nav>Discovery · Watchlist · Administration</nav></header>
    <main>
      {cacheFixture && <p role="status"><strong>Offline fictional cache test.</strong> All films, metadata and services shown here are synthetic; this does not exercise live enrichment.</p>}
      <div className="intro"><div><span className="eyebrow">YOUTRACK · LOCAL POC</span><h1>Film discovery</h1><p>Shared film records and separate personal preferences.</p></div></div>
      <div className="project"><label>Project<select value={project || ""} disabled={locked || cacheFixture} onChange={(e) => selectProject(e.target.value)}><option value="" disabled>Loading project…</option>{!cacheFixture && <option value="FILMREAL">Film collection</option>}<option value="FILMPOC">Synthetic test films</option></select></label><button disabled={locked || !project} onClick={() => refresh()}>Reload</button><a href="/issues" target="_blank" rel="noreferrer">Open tracker administration ↗</a></div>
      {hasPageDraft && <p role="status">You have unsaved edits. Save or copy them before reloading the browser or leaving YouTrack; this page cannot warn you when you reload.</p>}
      {error && <p role="alert">{error}</p>}{notice && <p className="notice">{notice}</p>}
      {liveRateLimited && <p role="alert">TMDB rate limit reached. Wait and reload the page before trying live lookups again.</p>}
      {pendingNavigation && <section aria-labelledby="discard-title"><h2 id="discard-title">Discard unsaved edits?</h2><p>Your film and preference drafts have not been saved.</p><button disabled={busy || restoringLocation} autoFocus onClick={() => setQueued(null)}>Keep editing</button><button disabled={busy || restoringLocation} onClick={() => {const target = pendingNavigation; setQueued(null); if (target.kind === "film") selectFilm(target.value, true); else if (target.kind === "project") selectProject(target.value, true); else navigateRoute(target.value);}}>Discard and continue</button></section>}
      {pendingPreview && <section aria-labelledby="preference-preview-title"><h2 id="preference-preview-title">Review preference changes</h2><p>Film: {pendingPreview.issue_id}</p><p>Interest: {preferenceLabel((pendingPreview.before || emptyPreference).interest_score)} → {preferenceLabel(pendingPreview.after.interest_score)}</p><p>Watchlist: {preferenceLabel((pendingPreview.before || emptyPreference).watchlist)} → {preferenceLabel(pendingPreview.after.watchlist)}</p><p>Watched date: {preferenceLabel((pendingPreview.before || emptyPreference).watched_at)} → {preferenceLabel(pendingPreview.after.watched_at)}</p><p>Notes before: {(pendingPreview.before || emptyPreference).personal_notes || "(empty)"}</p><p>Notes after: {pendingPreview.after.personal_notes || "(empty)"}</p><button disabled={busy || restoringLocation} autoFocus onClick={discardPreference}>Cancel preview</button><button disabled={busy || restoringLocation || saveUncertain || !previewMatchesFilm(pendingPreview, selected)} onClick={confirmPreference}>Save local preference</button>{discardFailed && <><p>The server preview may remain until another preview or app removal. Draft notes are not stored in it.</p><button disabled={busy || restoringLocation} onClick={() => {setPreview(null); setDiscardFailed(false); setNotice(saveUncertain ? "Preview closed locally; the save outcome and server preview remain unverified. Open a new preview to compare the server's Before value." : "Preview closed locally; the server preview may remain."); setSaveUncertain(false);}}>Close preview locally</button></>}</section>}
      {film ? <section>
        <button disabled={locked} onClick={() => selectFilm(null)}>← Back to films</button>
        <h2>{film.summary}</h2><p>{film.idReadable} · {filmYearLabel(film)}</p>
        <p>{field(film, "FilmIQ Director") ? `Source-listed director: ${field(film, "FilmIQ Director")}` : "Director unknown"}</p>
        {watchedHistory ? <section>
          <h3>Watched in Movary</h3><p>Snapshot observed {watchedHistory.observedAt || "time unknown"}. Watch dates and counts come from Movary; unknown dates remain unknown.</p>
          {watchedHistory.plays === null ? <p>Play entries unavailable.</p> : watchedHistory.plays.length ? <ul>{watchedHistory.plays.map((entry, index) => <li key={index}>{entry.date || "Date unknown"} · {entry.plays} play(s)</li>)}</ul> : <p>No play entries in this snapshot.</p>}
          {watchedHistory.exportDates === null ? <p>History export dates unavailable.</p> : watchedHistory.exportDates.length ? <p>History export dates: {watchedHistory.exportDates.map((date) => date || "unknown").join(", ")}. This is a separate source and is not added to play counts.</p> : <p>No history export dates in this snapshot.</p>}
        </section> : <p>Movary watched status unknown.</p>}
        {!cacheFixture && <ReviewedCatalog source="youtrack" filmId={film.idReadable} tmdbId={suppliedTmdbId(film)} trackerTitle={film.summary} host={host} />}
        <h3>{cacheFixture ? "Fictional cached details" : "Live TMDB details"}</h3>
        <p>{cacheFixture ? "Offline fictional data, read from the project-local fixture cache." : liveCache ? "Optional lookup for the supplied TMDB ID; verify that the result matches this film. Details may reappear from a local cache for up to seven days; they are not saved to YouTrack." : "Optional lookup for the supplied TMDB ID; verify that the result matches this film. Results stay in this page and are not saved to YouTrack."}</p>
        <button type="button" disabled={locked || liveBusy || liveRateLimited || !suppliedTmdbId(film)} onClick={loadLiveMetadata}>{liveBusy ? "Loading metadata…" : cacheFixture ? "Read fictional cache" : "Load live metadata"}</button>
        {!suppliedTmdbId(film) && <p>A supplied TMDB ID is required.</p>}
        {liveEntry?.error && <p role="alert">{liveEntry.error}</p>}
        {suppliedTmdbId(film) && !live && !liveEntry?.error && <MetadataUnavailable cached={liveCache || cacheFixture} />}
        {live && <section>
          {!liveMatches ? <IdentityReview expectedId={suppliedTmdbId(film)} savedTitle={film.summary} sourceYear={field(film, "FilmIQ Source Year")} sourceDirector={field(film, "FilmIQ Director")} data={live} provider={cacheFixture ? "Fictional cache" : "TMDB"} /> : <>
            <p>{cacheFixture ? "Fictional cache returned" : "TMDB returned"}: {live.title} ({live.year ?? "year unknown"}).</p>
            {live.original_title && <p>TMDB original title: {live.original_title} (identity not independently verified).</p>}
            {live.metadata_attempt && <p>Latest metadata was incomplete; earlier details are shown.</p>}
            {live.poster_url && <div className="poster"><Poster url={live.poster_url} alt={`TMDB poster for ${live.title}`} transient={liveCache} /></div>}
            {live.poster_from_previous && <p>Poster from an earlier lookup.</p>}
            <p>Directors: {live.directors?.join(", ") || "unknown"}; genres: {live.genres?.join(", ") || "unknown"}.</p>
            <p>{live.synopsis || "TMDB synopsis unknown."}</p>
            <p>US provider status: {live.availability.status}. {live.availability.offers.map((offer) => `${offer.provider} (${offer.kind})`).join(", ") || (live.availability.status === "complete" ? "No offers reported." : "Availability unknown.")} {availabilityTimeLabel(live.availability.status, live.availability.checked_at)}. Personal subscription entitlement is not established.</p>
            {live.availability_attempt && <p>Latest provider check was {live.availability_attempt}; the earlier provider observation is shown.</p>}
            {live.availability.provider_url && <ExternalLink url={live.availability.provider_url} label="Provider information on TMDB" />}
            {live.imdb_title_url && <p><ExternalLink url={live.imdb_title_url} label="IMDb title page" /> · supplied by TMDB; match not independently verified.</p>}
          </>}
          {!cacheFixture && <TmdbCredits />}
        </section>}
        <h3>Streaming availability</h3>
        <p>{observation ? `${observation.source} observation: ${observation.status}. ${availabilityTimeLabel(observation.status, observation.checked_at)}.` : "Availability unknown."}</p>
        <p>Subscriptions: {providerDescription(observation, "subscription")}. Rentals: {providerDescription(observation, "rent")}.</p>
        <form onSubmit={saveFilm} onKeyDown={(e) => submitOnEnter(e, saveFilm)}><label>Title<input value={title} required disabled={filmEditLocked} onChange={(e) => {setTitle(e.target.value); markFilmDirty(true);}} /></label><label>Supplied TMDB ID (optional)<input inputMode="numeric" value={tmdbId} disabled={filmEditLocked} onChange={(e) => {setTmdbId(e.target.value); markFilmDirty(true);}} /></label><label>Stored release year<input inputMode="numeric" value={releaseYear} disabled={filmEditLocked || !editBaseline?.yearEditable} onChange={(e) => {setReleaseYear(e.target.value); markFilmDirty(true);}} /></label><label>Stored genres (one per line)<textarea value={filmGenre} disabled={filmEditLocked || !editBaseline?.genreEditable} onChange={(e) => {setFilmGenre(e.target.value); setGenreReset(false); markFilmDirty(true);}} /></label>{editBaseline?.genreStatus === "known" && editBaseline.genre === "" && filmGenre === "" && <p>No stored genres. <button type="button" disabled={filmEditLocked || !editBaseline.genreEditable} onClick={() => {setGenreReset(true); markFilmDirty(true);}}>Set genres to unknown</button>{genreReset && " Will reset when saved."}</p>}<label>Synopsis<textarea value={synopsis} disabled={filmEditLocked} onChange={(e) => {setSynopsis(e.target.value); markFilmDirty(true);}} /></label><label>Lifecycle<select value={state} disabled={filmEditLocked} onChange={(e) => {setState(e.target.value); markFilmDirty(true);}}><option value="">Unknown</option>{states.map((s) => <option key={s}>{s}</option>)}</select></label>{filmDirty && <DraftExitWarning kind="film edits" />}<button type="button" onClick={saveFilm} disabled={filmEditLocked}>Save film</button></form>
        {(!editBaseline?.yearEditable || !editBaseline?.genreEditable) && <p>Release year or genre cannot be edited because its project field is unavailable or invalid.</p>}
        <p>Stored year and genre are editable fields; clearing either leaves it unknown and does not change source-listed assertions.</p>
        <p>Supplied IDs are unverified. Duplicate checks cover visible project records; live lookup remains subject to existing authorization. Clearing an existing ID is not supported in this POC.</p>
        <p>Changing a title does not independently verify the saved external identity or update its original source provenance.</p>
        <CriticFields score={field(film, "FilmIQ Critic Score")} summary={field(film, "FilmIQ Critic Summary")?.text} />
        <h3>Personal POC preferences</h3>
        <p>Saved local watched status: {localWatchLabel(preferences, film.idReadable)}. This is separate from the Movary snapshot.</p>
        {preferences === null ? <p>Preferences are loading or unavailable.</p> : <form onSubmit={savePreference} onKeyDown={(e) => submitOnEnter(e, savePreference)}>
          <label>Interest (1–10)<input type="number" min="1" max="10" disabled={locked} value={pref.interest_score ?? ""} onChange={(e) => changePreference({ interest_score: e.target.value === "" ? null : Number(e.target.value) })} /></label>
          <label>Local POC watchlist<select disabled={locked} value={pref.watchlist === null ? "unknown" : pref.watchlist ? "yes" : "no"} onChange={(e) => changePreference({ watchlist: e.target.value === "unknown" ? null : e.target.value === "yes" })}><option value="unknown">Unknown</option><option value="yes">Yes</option><option value="no">No</option></select></label>
          <label>Watched timestamp (UTC)<input type="datetime-local" disabled={locked} value={pref.watched_at ? pref.watched_at.slice(0, 16) : ""} onChange={(e) => changePreference({ watched_at: e.target.value ? new Date(`${e.target.value}Z`).toISOString() : null })} /></label>
          <label>Personal notes<textarea disabled={locked} value={pref.personal_notes} onChange={(e) => changePreference({ personal_notes: e.target.value })} /></label>{prefDirty && <DraftExitWarning kind="preferences" />}<button type="button" onClick={savePreference} disabled={locked}>Preview preference changes</button><p className="notice">Local experiment only; Movary remains authoritative.</p>
        </form>}
        <h3>Source evidence</h3>{sourceEvidenceState.status === "mismatch" && <p role="alert">The supplied TMDB ID differs from the original source evidence. Links are hidden until reviewed; source-listed year and director may refer to the previous ID.</p>}{sourceLinks.length ? <ul>{sourceLinks.map((item, index) => { const url = safeLink(item.url); return <li key={index}>{url ? <ExternalLink url={url} label={item.source_id || "Source"} /> : "Source link unavailable"} · {item.kind || "type unknown"} · lineage: {item.lineage_kind || "unknown"}</li>; })}</ul> : <p>Accepted source evidence unavailable.</p>}
        <h3>Direct reviews and aggregators</h3>{staleReviews ? <p>The film title differs from the reviewed source title; links are hidden until revalidated.</p> : reviews?.length ? <ul>{reviews.map((link, index) => <li key={index}><ExternalLink url={safeReviewUrl(link.url)} label={link.provider} /> · {link.type === "individual_critic_review" ? "Individual critic review" : "Review aggregator title page"} · checked {link.checked_at}<ReviewIdentity evidence={link.identity_evidence} /></li>)}</ul> : <p>Direct review links unavailable; coverage is unknown.</p>}
        <h3>Comments</h3>{comments === null ? <p>Comments unavailable.</p> : <ul>{comments.map((item) => <li key={item.id}>{item.author?.name || "Unknown"}: {item.text}</li>)}</ul>}
        <form onSubmit={addComment}><label>Add comment<textarea disabled={locked} value={commentDrafts[film.idReadable] || ""} onChange={(e) => setCommentDrafts((drafts) => ({...drafts, [film.idReadable]: e.target.value}))} /></label>{commentDrafts[film.idReadable]?.trim() && <DraftExitWarning kind="comments" />}<button type="button" onClick={addComment} disabled={locked}>Add comment</button></form>
        <a href={`/issue/${film.idReadable}`} target="_blank" rel="noreferrer">View tracker record and history ↗</a>
      </section> : <section>
        <div className="filters">
          <label>Search<input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Title or director" aria-description="Search by title or director" /></label>
          <label>Lifecycle<select value={stateFilter} onChange={(e) => setStateFilter(e.target.value)}><option value="">{showArchived ? "All states" : "Active states"}</option>{states.map((s) => <option key={s}>{s}</option>)}</select></label>
          <label><input type="checkbox" checked={showArchived} onChange={(e) => setShowArchived(e.target.checked)} /> Show archived</label>
          <label><input type="checkbox" checked={titleReviewOnly} onChange={(e) => setTitleReviewOnly(e.target.checked)} /> Title differences to review</label>
          <label>Genre<select value={genre} onChange={(e) => setGenre(e.target.value)}><option value="">All genres</option>{genres.map((g) => <option key={g}>{g}</option>)}</select></label>
          <label>Provider<select value={provider} onChange={(e) => setProvider(e.target.value)}><option value="">All providers</option>{providers.map((p) => <option key={p}>{p}</option>)}</select></label>
          <label>Availability freshness<select value={freshness} onChange={(e) => setFreshness(e.target.value)}><option value="">Any freshness</option><option value="recent">Checked within 7 days</option><option value="stale">Older than 7 days</option><option value="unknown">Unknown</option></select></label>
          <label>Minimum interest<input type="number" min="1" max="10" value={minimum} disabled={preferences === null && !minimum} onChange={(e) => setMinimum(e.target.value)} /></label>
          <label>Local watched status<select value={localWatched} disabled={preferences === null && !localWatched} onChange={(e) => setLocalWatched(e.target.value)}><option value="">Any status</option><option value="watched">Watched timestamp recorded</option><option value="not_recorded">No watched timestamp recorded</option><option value="unknown">Unknown</option></select></label>
          <label><input type="checkbox" checked={watchlistOnly} disabled={preferences === null && !watchlistOnly} onChange={(e) => setWatchlistOnly(e.target.checked)} /> Watchlist only</label>
          <label><input type="checkbox" checked={movaryOnly} disabled={movary?.status !== "available" && !movaryOnly} onChange={(e) => {setMovaryOnly(e.target.checked); if (e.target.checked) setExcludeMovaryWatched(false);}} /> Watched in Movary</label>
          <label><input type="checkbox" checked={excludeMovaryWatched} disabled={movary?.status !== "available" && !excludeMovaryWatched} onChange={(e) => {setExcludeMovaryWatched(e.target.checked); if (e.target.checked) setMovaryOnly(false);}} /> Exclude known watched in Movary</label>
          <label><input type="checkbox" checked={sortInterest} disabled={preferences === null && !sortInterest} onChange={(e) => setSortInterest(e.target.checked)} /> Sort by interest</label>
        </div>
        {query && <p>Director search uses source-listed or loaded live metadata; films with unknown directors may be missing.</p>}
        <p>{cacheFixture ? "Fictional cache details can reappear after reload until they expire." : liveCache ? "Cached film details can reappear after reload until they expire, up to seven days." : "Live film details stay available until you close or reload this page."}</p>
        <button type="button" disabled={locked || liveBusy || liveRateLimited || !eligibleLiveFilms(visible, liveResults).length} onClick={() => loadNextLiveBatch()}>{liveBatch ? `Loading ${liveBatch.done}/${liveBatch.total}…` : "Load live metadata for next 30 displayed films"}</button>{" "}
        <button type="button" disabled={locked || liveBusy || liveRateLimited || !remainingVisible.length} onClick={() => loadNextLiveBatch(true)}>Load all {remainingVisible.length} remaining visible films (up to {remainingVisible.length * 3} requests)</button>{" "}
        {incompleteMetadataFilter && <><p>Active metadata filters can exclude films with unknown metadata, so results may be incomplete. Loading the remaining project films also includes hidden and archived films; failed films require retry, and films without a supplied ID cannot be loaded. Title review only identifies loaded title differences; it does not verify matches.</p><button type="button" disabled={locked || liveBusy || liveRateLimited || !remainingProject.length} onClick={() => loadNextLiveBatch(true, false, true)}>Load all {remainingProject.length} remaining project films, including archived (up to {remainingProject.length * 3} TMDB API requests, plus poster images)</button>{" "}</>}
        {failedFilms.length > 0 && <button type="button" disabled={locked || liveBusy || liveRateLimited} onClick={() => loadNextLiveBatch(false, true)}>Retry {failedFilms.length} failed films in this project</button>}{" "}
        {liveBatch && <button type="button" onClick={() => {liveCancel.current = true;}}>Cancel loading</button>}
        {liveSummary && <p role="status">{liveSummary}</p>}
        {preferences === null && localWatched && <p role="status">Local watched filtering is unavailable while preferences are loading or unavailable.</p>}
        <h2>Discovery · {visible.length}</h2><div className="grid">{visible.map((item) => {const metadata = item.live; const poster = metadata?.poster_url; const available = providerObservation(item); const year = filmYearLabel(item, metadata?.year); const refresh = refreshNotice(liveResults[item.idReadable], suppliedTmdbId(item), metadata); return <button className="card" key={item.id} disabled={locked} onClick={() => selectFilm(item.idReadable)}><span className="poster"><Poster url={poster} alt={`TMDB poster for ${metadata?.title}`} loading="lazy" transient={liveCache} /></span><strong>{item.summary}</strong>{item.titleNeedsReview && <small>Title differs from TMDB; open to review.</small>}<small>{storedGenreDisplay(field(item, "FilmIQ Genre")) ?? (metadata?.genres?.join(", ") || "Genre unknown")}</small><small>{year} · Interest {preferences?.[item.idReadable]?.interest_score ?? "unknown"} · Critic score (source not recorded) {criticScore(field(item, "FilmIQ Critic Score"))}</small><small>{field(item, "FilmIQ Lifecycle")?.name || "State unknown"} · {movary?.status === "available" && movary?.films?.[item.idReadable]?.watched ? "Watched in Movary" : "Movary watched status unknown"}</small><small>{localWatchlistLabel(preferences, item.idReadable)} · Local watched status: {localWatchLabel(preferences, item.idReadable)}</small><small>{available?.source || "Provider"} subscriptions: {providerDescription(available, "subscription")}</small>{metadata?.poster_from_previous && <small>Poster from an earlier lookup.</small>}{refresh && <small>{refresh}</small>}{metadata && <small>Supplied TMDB identity is unverified.</small>}</button>;})}</div>
        {Object.values(liveResults).some((item) => item.data) && <TmdbCredits />}
        <form onSubmit={addFilm} onKeyDown={(e) => submitOnEnter(e, addFilm)}><label>Add film title<input disabled={locked} value={newTitle} onChange={(e) => setNewTitle(e.target.value)} /></label><label>Supplied TMDB ID (optional)<input inputMode="numeric" disabled={locked} value={newTmdbId} onChange={(e) => setNewTmdbId(e.target.value)} /></label><p>IDs are unverified. Duplicate checks cover visible project records; live lookup remains subject to existing authorization.</p>{(newTitle.trim() || newTmdbId.trim()) && <DraftExitWarning kind="new-film details" />}<button type="button" onClick={addFilm} disabled={locked || !project || createUncertain}>Add film</button></form>
      </section>}
    </main>
  </>;
}

if (typeof document !== "undefined") createRoot(document.getElementById("root")).render(<App />);
