# YouTrack film-save recovery

The installed widget blocks film editing and another save after a YouTrack film
write has an unconfirmed outcome or a confirmed write cannot be followed by a
successful film reload. It retains text drafts as selectable, read-only values.
The explicit recovery action reloads films and discards the film draft only
when the reload succeeds. The guard also remains in place when navigating away
from and back to a film or project. This prevents an old edit baseline from
silently suppressing a later change or overwriting an unrelated update.

Fictional handler checks cover write and reload failures, blocked retries,
failed recovery, route changes, and explicit successful reload/discard. This
widget package matched the reviewed build after an in-place update. The full
watched property, watched projections, preferences, app settings, usages and
attachment metadata were unchanged in the checked snapshots. The real-film
browser behavior has not been verified.

This was a combined YouTrack and Kaneo UI update, which also installed the
provider-denial messages. The separate enrichment bridge update was still
pending at the time of this UI deployment; the UI update alone does not prove
that a provider denial reaches the browser.

```sh
node docs/research/tracker-poc/ui/youtrack_save_workflow_check.mjs
node docs/research/tracker-poc/ui/youtrack_navigation_check.mjs
```
