# ADR 0001 — Movary owns personal state

**Date:** 2026-10-29  
**Status:** Accepted; interface clarified 2026-11-04

## Context
Movary already tracks watches, dates, ratings and an intentional watchlist.

## Decision
Keep Movary as authoritative for watched dates, plays, enjoyment ratings and
intentional watchlist. FilmIQ reads authenticated API/export state and presents
it in its recommendation UI. Explicit UI actions may log a selected date through
the supported API and preview/confirm a watchlist addition. No automatic
suggestion promotion. Its local saved/dismissed recommendation dispositions are
not a competing intentional watchlist.

## Consequences
No second personal-state store, direct Movary database edits, silent deletion or
mass promotion. Existing dates/plays/comments survive a new-date action; retries
must not increment plays. Surface Movary's possible automatic watchlist removal
before confirming a watch. Personal writes require API readback; a later refresh
failure must not be represented as rollback or an up-to-date cache.

Movary 0.82.1 has no bearer-token rating-write endpoint. The user's subsequent
request for **Rate & mark watched** authorizes a small configured command bridge
to the same `MovieApi.updateUserRating` application service used by its native
rating controller. The request travels as JSON on stdin; the service resolves
user/film and verifies its saved rating. No direct SQL, remote project file,
session-login automation, fork or second personal store is introduced. This
bridge is explicitly version-specific and must be checked on Movary upgrades.
The native film editor remains available when the bridge is not configured.

## Validation / reconsideration
Reconsider only if a documented core Movary limitation persists after a working companion POC.

