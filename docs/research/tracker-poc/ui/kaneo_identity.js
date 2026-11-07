import { tmdbId } from "./live_batch.js";
import { matchesLiveTitle } from "./youtrack_tmdb.js";

export function matchedLive(film, result) {
  const data = result?.data;
  return tmdbId(film) && data?.tmdb_id === tmdbId(film) && matchesLiveTitle(film.title, data) ? data : null;
}

export async function identityField(request, project, value, taskId = null) {
  if (!/^[1-9][0-9]{0,9}$/.test(value) || Number(value) > 2147483647)
    throw new Error("TMDB ID must be a positive integer up to 2147483647.");
  const base = `/custom-field/project/${encodeURIComponent(project)}`;
  const definitions = await request(base);
  const matches = definitions.filter((field) => field.name === "POC TMDB ID");
  if (matches.length !== 1 || matches[0].type !== "text") throw new Error("This project needs exactly one text field named POC TMDB ID.");
  const rows = await request(`${base}/values`);
  if (rows.some((row) => row.fieldId === matches[0].id && row.value === value && row.taskId !== taskId))
    throw new Error("That TMDB ID already belongs to a film in this project.");
  return matches[0].id;
}

export class CreatedFilmUnverified extends Error {}

export async function createFilm(request, project, payload, fieldId, value) {
  const created = await request(`/task/${encodeURIComponent(project)}`, "POST", payload);
  if (!created?.id) throw new Error("Kaneo did not return the created film ID.");
  if (fieldId) {
    try {
      const values = await request(`/custom-field/task/${encodeURIComponent(created.id)}`);
      const identity = values.filter((row) => row.fieldId === fieldId);
      if (identity.length !== 1 || identity[0].value !== value)
        throw new Error("ID not confirmed");
    } catch {
      throw new CreatedFilmUnverified(`Film ${created.id} was created, but its TMDB ID could not be confirmed. Open that film and check its ID before retrying.`);
    }
  }
  return created;
}
