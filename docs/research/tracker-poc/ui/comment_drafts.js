// A draft belongs to the film where it was written, including after a save.
export function setCommentDraft(drafts, filmId, text) {
  return { ...drafts, [filmId]: text };
}

export function clearSavedDraft(drafts, filmId, savedText) {
  return drafts[filmId] === savedText ? setCommentDraft(drafts, filmId, "") : drafts;
}

export function currentComments(selectedId, targetId, existing, updated) {
  return selectedId === targetId ? updated : existing;
}
