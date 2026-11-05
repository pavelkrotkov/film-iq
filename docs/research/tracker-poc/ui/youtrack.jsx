import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";

// The host injects YTApp and authorizes each call as the signed-in user.
const host = await YTApp.register();
const fields = "id,idReadable,summary,description,project(id,shortName)";

function App() {
  const [project, setProject] = useState("FILMPOC");
  const [films, setFilms] = useState([]);
  const [selected, setSelected] = useState(null);
  const [synopsis, setSynopsis] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function load() {
    setBusy(true);
    setError("");
    try {
      const all = [];
      const ids = new Set();
      const pageSize = 100;
      for (let skip = 0; ; ) {
        const page = await host.fetchYouTrack("issues", {
          query: { fields, query: `project: {${project}} sort by: id asc`, $top: pageSize, $skip: skip },
        });
        if (!Array.isArray(page)) throw new Error("Unexpected issue response");
        if (!page.length) break;
        for (const film of page) {
          if (!film.id || ids.has(film.id)) throw new Error("Issue pagination was inconsistent; reload the project.");
          ids.add(film.id);
        }
        all.push(...page);
        skip += page.length;
      }
      setFilms(all);
    } catch (e) {
      setError(`Could not load issues: ${e.message}`);
    } finally {
      setBusy(false);
    }
  }
  useEffect(() => { load(); }, []);

  async function save() {
    setBusy(true);
    setError("");
    try {
      await host.fetchYouTrack(`issues/${encodeURIComponent(selected.id)}`, {
        method: "POST", query: { fields }, body: { description: synopsis },
      });
      setSelected(null);
      await load();
    } catch (e) {
      setError(`Could not save synopsis: ${e.message}`);
    } finally {
      setBusy(false);
    }
  }

  return <main>
    <header><h1>FilmIQ · YouTrack experiment</h1><p>Synthetic records only. This is an incomplete POC.</p></header>
    <label>Project key <input value={project} onChange={(e) => setProject(e.target.value)} /></label>{" "}
    <button disabled={busy} onClick={load}>Load films</button>
    {error && <p role="alert">{error}</p>}
    {selected ? <section>
      <button onClick={() => setSelected(null)}>Back to films</button>
      <h2>{selected.summary}</h2><p>{selected.idReadable}</p>
      <label>Synopsis <textarea value={synopsis} onChange={(e) => setSynopsis(e.target.value)} /></label>
      <button disabled={busy} onClick={save}>Save synopsis</button>
    </section> : <section><h2>Discovery · {films.length}</h2><div className="grid">
      {films.map((film) => <button className="card" key={film.id} onClick={() => { setSelected(film); setSynopsis(film.description || ""); }}>
        <span className="poster">Artwork unavailable</span><strong>{film.summary}</strong><small>{film.idReadable}</small>
      </button>)}
    </div></section>}
  </main>;
}

createRoot(document.getElementById("root")).render(<App />);
