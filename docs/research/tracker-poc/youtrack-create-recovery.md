# YouTrack film-creation recovery

The installed widget blocks another film creation after an unconfirmed write
or a confirmed creation whose film-list reload fails. It preserves the title
and optional ID draft, requires a successful reload in the original project,
then asks the user to check the list and explicitly allow another attempt.
The warning notes that filters can hide films. A failed reload or a different
project cannot clear the guard.

Fictional tests exercise the actual handler for ID-less failed writes,
incomplete acknowledgments, failed and successful reloads, draft retention,
cross-project checks and explicit retry confirmation. The guard is held in page
memory, so a full page reload clears it. Checking cannot guarantee exactly-once
creation if a timed-out request completes after the check; the API has no
demonstrated idempotency key or uniqueness constraint. The in-place app update
matched the independently reviewed package on readback; the complete watched
property, projections, preferences, settings, usages and attachment metadata
were unchanged in the checked snapshots. The real-film browser behavior has
not been verified.

```sh
node docs/research/tracker-poc/ui/youtrack_create_guard_check.mjs
```
