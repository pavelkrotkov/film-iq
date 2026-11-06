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
  let film = kind === "kaneo" ? {id} : {id:"fictional-issue",idReadable:id};
  let drafts = {[id]: "Fictional comment"}, comments = ["Earlier"], error = "", posts = 0, reads = 0, recovery = {}, currentMode = mode;
  const selected = {current:id};
  const post = async () => { posts++; if (currentMode === "post-fails") throw new Error("Fictional post failure"); };
  const reload = async () => { reads++; if (currentMode === "read-fails") throw new Error("Fictional read failure"); return ["Fictional comment"]; };
  const setters = {
    setError: value => { error = value; },
    setCommentDrafts: update => { drafts = update(drafts); },
    setComments: update => { comments = typeof update === "function" ? update(comments) : update; },
    setCommentRecovery: update => { recovery = update(recovery); },
  };
  const handlers = () => {
    if (kind === "kaneo") {
      const source = handlerSource("./src.jsx", "startLiveBatch");
      const make = new Function("film", "commentDrafts", "commentRecovery", "setCommentRecovery", "setBusy", "setError", "request", "setCommentDrafts", "setComments", "selectedRef", "saveComment", "clearSavedDraft", "currentComments", `${source}; return {addComment, reviewComment, allowCommentRetry};`);
      return make(film, drafts, recovery, setters.setCommentRecovery, () => {}, setters.setError, async (_path, method) => method === "POST" ? post() : reload(), setters.setCommentDrafts, setters.setComments, selected, saveComment, clearSavedDraft, currentComments);
    }
    const source = handlerSource("./youtrack.jsx", "addFilm");
    const make = new Function("film", "commentDrafts", "commentRecovery", "setCommentRecovery", "setWorking", "setError", "host", "setCommentDrafts", "getComments", "selectedRef", "setComments", "saveComment", "clearSavedDraft", "currentComments", `${source}; return {addComment, reviewComment, allowCommentRetry};`);
    return make(film, drafts, recovery, setters.setCommentRecovery, () => {}, setters.setError, {fetchYouTrack:post}, setters.setCommentDrafts, reload, selected, setters.setComments, saveComment, clearSavedDraft, currentComments);
  };
  const click = async (action) => handlers()[action]({preventDefault() {}});
  await click("addComment");
  const select = (next) => {
    film = kind === "kaneo" ? {id:next} : {id:`issue-${next}`,idReadable:next};
    selected.current = next;
    if (!Object.hasOwn(drafts, next)) drafts[next] = "Another fictional comment";
  };
  return {get draft() {return drafts[id];}, get comments() {return comments;}, get error() {return error;}, get posts() {return posts;}, get reads() {return reads;}, get recovery() {return recovery[id];}, click, setMode: value => {currentMode = value;}, selected, select};
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
  assert.equal(postFailure.recovery, "pending");
  await postFailure.click("addComment"); assert.equal(postFailure.posts, 1, "uncertain save blocks duplicate retry");
  postFailure.setMode("read-fails"); await postFailure.click("reviewComment");
  assert.equal(postFailure.recovery, "pending", "failed reload keeps retry blocked");
  await postFailure.click("allowCommentRetry"); assert.equal(postFailure.recovery, "pending");
  postFailure.setMode("success");
  postFailure.selected.current = "different-film"; await postFailure.click("reviewComment");
  assert.equal(postFailure.recovery, "pending", "a reload completed after navigation cannot count as checked");
  postFailure.selected.current = kind === "kaneo" ? "fictional-task" : "FILMPOC-1";
  await postFailure.click("reviewComment"); assert.equal(postFailure.recovery, "checked");
  assert.equal(postFailure.draft, "Fictional comment", "reload preserves the draft");
  await postFailure.click("addComment"); assert.equal(postFailure.posts, 1, "review alone does not permit retry");
  await postFailure.click("allowCommentRetry"); assert.equal(postFailure.recovery, undefined);
  await postFailure.click("addComment"); assert.equal(postFailure.posts, 2); assert.equal(postFailure.draft, "");
  const isolated = await exercise(kind, "post-fails");
  isolated.setMode("success"); isolated.select(kind === "kaneo" ? "other-task" : "FILMPOC-2");
  await isolated.click("addComment"); assert.equal(isolated.posts, 2, "another film remains usable");
  isolated.select(kind === "kaneo" ? "fictional-task" : "FILMPOC-1");
  await isolated.click("addComment"); assert.equal(isolated.posts, 2, "returning to the uncertain film remains blocked");
  assert.equal(isolated.draft, "Fictional comment");
}
console.log("Both comment workflows preserve drafts and guard uncertain retries");
