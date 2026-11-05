import assert from "node:assert/strict";
import { clearSavedDraft, currentComments, setCommentDraft } from "./comment_drafts.js";

let drafts = setCommentDraft({}, "film-a", "Thoughts on A");
assert.equal(drafts["film-b"] ?? "", "", "A's draft must not appear on B");
drafts = setCommentDraft(drafts, "film-b", "Thoughts on B");
drafts = clearSavedDraft(drafts, "film-a", "Thoughts on A");
assert.equal(drafts["film-b"], "Thoughts on B", "Saving A must preserve B's draft");
drafts = setCommentDraft(drafts, "film-a", "New text");
assert.equal(clearSavedDraft(drafts, "film-a", "Old text")["film-a"], "New text", "A later edit must survive an earlier save");
const commentsB = ["B comment"], responseA = ["A comment"];
assert.equal(currentComments("film-b", "film-a", commentsB, responseA), commentsB, "A late response must not replace B's comments");
assert.equal(currentComments("film-a", "film-a", commentsB, responseA), responseA);
console.log("Per-film comment drafts and late response isolation passed");
