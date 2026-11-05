export const emptyPreference = {
  interest_score: null,
  watchlist: null,
  watched_at: null,
  personal_notes: "",
};

export function syncPreferenceDraft(draft, filmId, preferences) {
  if (draft.filmId === filmId && (draft.dirty || !preferences)) return draft;
  return { filmId, value: preferences?.[filmId] || emptyPreference, dirty: false };
}

export function markPreferenceSaved(draft, filmId, savedValue) {
  return draft.filmId === filmId && draft.value === savedValue ? { ...draft, dirty: false } : draft;
}

export function mergeFilmDraft(draft, loaded, dirty) {
  return dirty ? draft : { title: loaded.title, description: loaded.description, status: loaded.status, tmdb: loaded.tmdb || "" };
}
