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

## Preference confirmation

The installed widget checks the preference confirmation against the selected
film and the previewed values. Once the server acknowledges those values, it
retains them in the visible preference map even if the follow-up read fails or
returns a missing or different value. An invalid or unconfirmed response keeps
the draft and reports that the save may have completed. Fictional tests exercise
the actual handler for these outcomes and a selection change during confirmation.

The combined UI update was verified by installed-package and served-bundle
readback, with the complete watched property, projections, visible preferences,
settings, usages and attachment metadata unchanged. It did not write film or
preference records. This preference workflow has not been tested in a real-film
browser session.

```sh
node docs/research/tracker-poc/ui/youtrack_save_workflow_check.mjs
node docs/research/tracker-poc/ui/youtrack_navigation_check.mjs
node docs/research/tracker-poc/ui/youtrack_preference_confirm_check.mjs
```
