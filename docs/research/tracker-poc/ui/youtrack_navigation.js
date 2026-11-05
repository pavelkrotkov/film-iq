export function routeLocation(route) {
  const params = new URLSearchParams({project: route.project});
  if (route.film) params.set("film", route.film);
  return {search: params.toString()};
}

export function hasUnsavedPageDraft({filmDirty, prefDirty, commentDrafts, newTitle, newTmdbId}) {
  return Boolean(filmDirty || prefDirty || newTitle.trim() || newTmdbId.trim() ||
    Object.values(commentDrafts).some((text) => typeof text === "string" && text.trim()));
}

export async function handleExternalRoute(current, next, guards, {apply, queue, restore, notify}) {
  if (current.project === next.project && current.film === next.film) return;
  if (!current.project || !(guards.pendingPreview || guards.pendingNavigation || guards.busy || guards.filmDirty || guards.prefDirty)) {
    apply(next);
    return;
  }
  if (guards.pendingPreview) notify("Cancel or confirm the current preference preview before navigating.");
  else if (guards.pendingNavigation || guards.busy) notify("Finish the current action before navigating.");
  else queue(next);
  try { await restore(current); }
  catch { notify("Could not restore the current app location. Your screen and unsaved edits remain; the address may not match."); }
}
