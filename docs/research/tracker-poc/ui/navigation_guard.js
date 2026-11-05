// Only in-app controls use this guard; browser back/reload/close remain unverified.
export function confirmNavigation(filmDirty, preferenceDirty, confirm) {
  return !(filmDirty || preferenceDirty) || confirm("Discard unsaved film and preference edits?");
}
