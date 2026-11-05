import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  filterFilms,
  providers,
  syntheticAvailability,
} from "./film_filters.js";

const api = "http://localhost:15173/api";
const states = {
  "to-do": "Discovery",
  "in-progress": "Evaluation",
  "in-review": "Watchlist",
  done: "Done",
};

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

const emptyPreference = {
  interest_score: null,
  watchlist: false,
  watched_at: null,
  personal_notes: "",
};

async function load(project) {
  const id = encodeURIComponent(project);
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
  return films.map((film) => ({ ...film, fields: values.get(film.id) || {} }));
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
  const [selected, setSelected] = useState(selectedId),
    [query, setQuery] = useState(""),
    [provider, setProvider] = useState("");
  const [preferences, setPreferences] = useState(null),
    [preference, setPreference] = useState(emptyPreference),
    [watchlistOnly, setWatchlistOnly] = useState(false),
    [sortInterest, setSortInterest] = useState(false);
  const [minimum, setMinimum] = useState(""),
    [genre, setGenre] = useState(""),
    [lifecycle, setLifecycle] = useState(""),
    [watched, setWatched] = useState(""),
    [freshnessFilter, setFreshnessFilter] = useState("");
  const [description, setDescription] = useState(""),
    [status, setStatus] = useState(""),
    [detailReady, setDetailReady] = useState(false);
  async function refresh() {
    setBusy(true);
    setError("");
    try {
      setFilms(await load(project));
      try {
        setPreferences((await preferenceRequest("/preferences")).preferences);
      } catch (e) {
        setPreferences(null);
        setError(`Preferences are unavailable: ${e.message}`);
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
  const film = films.find((item) => item.id === selected);
  const genres = [
    ...new Set(films.map((item) => item.fields["POC Genre"]).filter(Boolean)),
  ].sort();
  const services = [
    ...new Set(films.flatMap((item) => providers(item) || [])),
  ].sort();
  useEffect(() => {
    setPreference(
      film && preferences
        ? preferences[film.id] || emptyPreference
        : emptyPreference,
    );
  }, [film, preferences]);
  useEffect(() => {
    let active = true;
    setDetailReady(false);
    if (film)
      request(`/task/${encodeURIComponent(film.id)}`)
        .then((detail) => {
          if (typeof detail.description !== "string")
            throw new Error(
              "Full synopsis is unavailable; editing is disabled.",
            );
          if (active) {
            setDescription(detail.description);
            setStatus(detail.status);
            setDetailReady(true);
          }
        })
        .catch((e) => {
          if (active) setError(e.message);
        });
    return () => {
      active = false;
    };
  }, [film]);
  const filtered = useMemo(
    () =>
      filterFilms(films, {
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
      }),
    [
      films,
      query,
      provider,
      watchlistOnly,
      sortInterest,
      preferences,
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
      const text = `Preview synthetic preference change:\nInterest: ${preview.before.interest_score ?? "unknown"} → ${preview.after.interest_score ?? "unknown"}\nWatchlist: ${preview.before.watchlist ? "yes" : "no"} → ${preview.after.watchlist ? "yes" : "no"}\nWatched: ${preview.before.watched_at || "not marked"} → ${preview.after.watched_at || "not marked"}\nNotes before: ${preview.before.personal_notes || "(empty)"}\nNotes after: ${preview.after.personal_notes || "(empty)"}\n\nSave these changes?`;
      if (window.confirm(text)) {
        await preferenceRequest(`/preferences/${path}`, "PUT", {
          preference,
          token: preview.token,
        });
        setPreferences((await preferenceRequest("/preferences")).preferences);
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
      await refresh();
    } catch (e) {
      setError(`Update may be partial. Reload to check: ${e.message}`);
      setBusy(false);
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
              A live view of synthetic films stored in your local Kaneo project.
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
          Synthetic data only. Preferences use a separate local POC store; they
          do not change Movary.
        </p>
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
                <span>NO POSTER</span>
              </div>
              <div>
                <div className="eyebrow">
                  {film.fields["POC Genre"] || "GENRE UNKNOWN"} ·{" "}
                  {film.fields["POC Year"] || "YEAR UNKNOWN"}
                </div>
                <h2>{film.title}</h2>
                <div className="badges">
                  {providers(film)?.length ? (
                    providers(film).map((name) => (
                      <span key={name}>{name}</span>
                    ))
                  ) : (
                    <span>Availability unknown</span>
                  )}
                </div>
                <form onSubmit={save}>
                  <label>
                    Synopsis
                    <textarea
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                      rows="7"
                      disabled={!detailReady}
                    />
                  </label>
                  <label>
                    Lifecycle
                    <select
                      value={status}
                      onChange={(e) => setStatus(e.target.value)}
                      disabled={!detailReady}
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
                  <h3>Your synthetic preferences</h3>
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
                    <span>
                      <input
                        type="checkbox"
                        checked={preference.watchlist}
                        disabled={!preferences}
                        onChange={(e) =>
                          setPreference({
                            ...preference,
                            watchlist: e.target.checked,
                          })
                        }
                      />{" "}
                      On my watchlist
                    </span>
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
                      Marked watched
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
                {syntheticAvailability(film) && (
                  <p>
                    Synthetic rentals:{" "}
                    {syntheticAvailability(film).rent.join(", ") ||
                      "None reported"}
                    . Checked:{" "}
                    {syntheticAvailability(film).checked_at || "Unknown"}.
                  </p>
                )}
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
                  disabled={!preferences}
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
                  aria-label="Filter by watched status"
                  value={watched}
                  disabled={!preferences}
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
                    disabled={!preferences}
                    onChange={(e) => setWatchlistOnly(e.target.checked)}
                  />{" "}
                  Watchlist
                </label>
                <label>
                  <input
                    type="checkbox"
                    checked={sortInterest}
                    disabled={!preferences}
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
                      <span>NO POSTER</span>
                      <b>{states[item.status] || item.status}</b>
                    </div>
                    <div className="card-body">
                      <div className="card-meta">
                        {item.fields["POC Genre"] || "UNKNOWN GENRE"} ·{" "}
                        {item.fields["POC Year"] || "UNKNOWN YEAR"}
                      </div>
                      <h3>{item.title}</h3>
                      <div className="badges">
                        {providers(item)?.length ? (
                          providers(item).map((name) => (
                            <span key={name}>{name}</span>
                          ))
                        ) : (
                          <span>Availability unknown</span>
                        )}
                      </div>
                      <p>
                        Critic score:{" "}
                        {item.fields["POC Critic Score"] || "Unknown"}
                      </p>
                      <p>
                        Interest:{" "}
                        {preferences
                          ? (preferences[item.id]?.interest_score ?? "Unknown")
                          : "Unavailable"}{" "}
                        ·{" "}
                        {preferences
                          ? preferences[item.id]?.watchlist
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
