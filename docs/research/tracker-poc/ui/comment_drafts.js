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

// A confirmed post remains saved even when the following read fails.
export async function saveComment(post, reload, onSaved) {
  await post();
  onSaved();
  try {
    return {refreshed: true, comments: await reload()};
  } catch {
    return {refreshed: false, comments: null};
  }
}
