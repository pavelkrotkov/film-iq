export function confirmNavigation(filmDirty, preferenceDirty, confirm) {
  return !(filmDirty || preferenceDirty) || confirm("Discard unsaved film and preference edits?");
}

export function selectedFromUrl(url) {
  return new URLSearchParams(new URL(url).hash.slice(1)).get("film");
}

export function sameTabClick(event) {
  return event.button === 0 && !event.metaKey && !event.ctrlKey && !event.shiftKey && !event.altKey;
}

export function hasCommentDrafts(drafts) {
  return Object.values(drafts).some((value) => typeof value === "string" && value.trim());
}

export function guardSameDocumentNavigation(event, selected, filmDirty, preferenceDirty, confirm) {
  if (!event.destination?.sameDocument || !event.cancelable ||
      selectedFromUrl(event.destination.url) === selected) return;
  if (!confirmNavigation(filmDirty, preferenceDirty, confirm)) event.preventDefault();
}
