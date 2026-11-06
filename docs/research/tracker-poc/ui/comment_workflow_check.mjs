import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {clearSavedDraft, currentComments, saveComment} from "./comment_drafts.js";

function handlerSource(name, next) {
  const source = readFileSync(new URL(name, import.meta.url), "utf8");
  const start = source.indexOf("  async function addComment(event) {");
  const end = source.indexOf(`  async function ${next}(`, start);
  if (start < 0 || end < 0) throw new Error("Comment handler not found");
  return source.slice(start, end);
}

async function exercise(kind, mode) {
  const id = kind === "kaneo" ? "fictional-task" : "FILMPOC-1";
  const film = kind === "kaneo" ? {id} : {id:"fictional-issue",idReadable:id};
  let drafts = {[id]: "Fictional comment"}, comments = ["Earlier"], error = "", posts = 0, reads = 0;
  const post = async () => { posts++; if (mode === "post-fails") throw new Error("Fictional post failure"); };
  const reload = async () => { reads++; if (mode === "read-fails") throw new Error("Fictional read failure"); return ["Fictional comment"]; };
  const setters = {
    setError: value => { error = value; },
    setCommentDrafts: update => { drafts = update(drafts); },
    setComments: update => { comments = typeof update === "function" ? update(comments) : update; },
  };
  let handler;
  if (kind === "kaneo") {
    const source = handlerSource("./src.jsx", "startLiveBatch");
    const make = new Function("film", "commentDrafts", "setBusy", "setError", "request", "setCommentDrafts", "setComments", "selectedRef", "saveComment", "clearSavedDraft", "currentComments", `${source}; return addComment;`);
    handler = make(film, drafts, () => {}, setters.setError, async (_path, method) => method === "POST" ? post() : reload(), setters.setCommentDrafts, setters.setComments, {current:id}, saveComment, clearSavedDraft, currentComments);
  } else {
    const source = handlerSource("./youtrack.jsx", "addFilm");
    const make = new Function("film", "commentDrafts", "setWorking", "setError", "host", "setCommentDrafts", "getComments", "selectedRef", "setComments", "saveComment", "clearSavedDraft", "currentComments", `${source}; return addComment;`);
    handler = make(film, drafts, () => {}, setters.setError, {fetchYouTrack:post}, setters.setCommentDrafts, reload, {current:id}, setters.setComments, saveComment, clearSavedDraft, currentComments);
  }
  await handler({preventDefault() {}});
  return {draft: drafts[id], comments, error, posts, reads};
}

for (const kind of ["kaneo", "youtrack"]) {
  const saved = await exercise(kind, "success");
  assert.equal(saved.draft, ""); assert.deepEqual(saved.comments, ["Fictional comment"]); assert.equal(saved.error, "");
  const readFailure = await exercise(kind, "read-fails");
  assert.equal(readFailure.posts, 1); assert.equal(readFailure.reads, 1); assert.equal(readFailure.draft, ""); assert.equal(readFailure.comments, null);
  assert.match(readFailure.error, /^Comment saved, but comments could not be reloaded/);
  const postFailure = await exercise(kind, "post-fails");
  assert.equal(postFailure.posts, 1); assert.equal(postFailure.reads, 0); assert.equal(postFailure.draft, "Fictional comment");
  assert.match(postFailure.error, /^Comment may have been saved/);
}
console.log("Both comment workflows distinguish an acknowledged save from a failed reload");
