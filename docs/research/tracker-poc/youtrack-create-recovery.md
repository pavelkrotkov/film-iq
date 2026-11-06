# YouTrack film-creation recovery candidate

The source candidate blocks another film creation after an unconfirmed write
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
demonstrated idempotency key or uniqueness constraint. The change has not yet
been deployed or verified in a real-film browser session.

```sh
node docs/research/tracker-poc/ui/youtrack_create_guard_check.mjs
```
