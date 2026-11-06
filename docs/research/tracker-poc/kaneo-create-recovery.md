# Kaneo film-creation recovery

The deployed Kaneo UI blocks another film creation after an unconfirmed write
or after a confirmed creation whose follow-up film reload fails. It keeps the
title and optional ID draft, requires a successful film-list reload, then asks
the user to check the list and explicitly allow another attempt. A failed reload
does not unblock creation. The inputs are disabled during creation and reload
so a new draft cannot be cleared by an earlier response.

Fictional tests exercise the actual handler for failed and successful writes,
failed and successful reloads, draft retention and explicit retry confirmation.
The installed bundle matched the reviewed build by on-disk and served-byte
readback, and an owner-only rollback bundle was retained in the project cache.
No tracker record was changed during deployment. The guard is in page memory;
a full browser reload clears it, and the existing unsaved-draft warning remains.
Real-film browser behavior has not been verified.

```sh
node docs/research/tracker-poc/ui/kaneo_create_guard_check.mjs
node docs/research/tracker-poc/ui/kaneo_identity_check.mjs
```
