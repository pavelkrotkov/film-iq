# YouTrack film-save recovery

The source candidate blocks film editing and another save after a YouTrack film
write has an unconfirmed outcome or a confirmed write cannot be followed by a
successful film reload. It retains text drafts as selectable, read-only values.
The explicit recovery action reloads films and discards the film draft only
when the reload succeeds. The guard also remains in place when navigating away
from and back to a film or project. This prevents an old edit baseline from
silently suppressing a later change or overwriting an unrelated update.

Fictional handler checks cover write and reload failures, blocked retries,
failed recovery, route changes, and explicit successful reload/discard. This
source change has not yet been deployed or verified in a real-film browser.

```sh
node docs/research/tracker-poc/ui/youtrack_save_workflow_check.mjs
node docs/research/tracker-poc/ui/youtrack_navigation_check.mjs
```
