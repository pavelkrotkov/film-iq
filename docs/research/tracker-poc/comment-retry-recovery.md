# Comment retry after an uncertain save

If either POC cannot confirm a comment POST, the draft remains on its film and
another POST for that film is blocked. Reload the comments, check whether the
draft was already saved, then explicitly allow another attempt if needed.
Other films remain usable. A failed reload or a reload completed after switching
films does not unlock the original comment.

The guard and unsaved drafts exist only in page memory: a full browser reload
clears them. A delayed server response can still complete after a user checks
the list, so this is not an exactly-once guarantee. Fictional actual-handler
tests cover both trackers, including failed reload, navigation, preserved
drafts and explicit retry. No real-film browser verification is claimed.

```sh
node docs/research/tracker-poc/ui/comment_workflow_check.mjs
```
