# YouTrack live metadata widget experiment

The widget can request one film, the next 30 displayed films, or all remaining
displayed films only after a user action. Bulk requests are sequential and stop
on any failed request, cancellation, or a project/refresh change. This also
stops a rate-limited batch when the Host API does not expose the HTTP status.
Failed films are not automatically retried; an individual film or the failed
films in the current project can be retried explicitly. The response is held in
page memory, not written to issue fields or preferences.

A fictional browser check returned one successful response followed by a
synthetic failure, then retried the failed film while a provider filter hid it.
The retry succeeded and retained the earlier successful result. No live
provider or tracker write was involved in that test.

This source expects a separately installed and configured issue-scoped handler
at `issues/{issueId}/extensionEndpoints/filmiq-tmdb-live-isolated/metadata/read`.
It sends a POST with an empty JSON body through `host.fetchYouTrack`. The
handler must authenticate the current user, validate issue access, enforce the
authorized film-ID allowlist and keep credentials server-side. The widget checks
that the response ID matches the issue's supplied ID, but this does not prove
that the supplied ID identifies the intended film. The handler and widget are
installed, and direct API checks passed for the approved set. In an isolated
browser, trusted keyboard activation of the same widget handler reached the
separately installed fictional fixture app and displayed its title and
synopsis. The browser test substituted fictional provider data and poster bytes
locally. This does not verify the production handler or a real poster through
the widget, and the synthetic pointer click was unreliable in that setup.
In a separate trusted-keyboard check, the actual fictional fixture returned 429;
the widget displayed a rate-limit message, disabled loading and made no second
request when activated again.
Grid artwork, provider data and live genre filters require the issue title to
match either the current TMDB title or original title after Unicode, case and
whitespace normalization. The original title is read from the same opt-in
response; it is not independently reviewed evidence. A mismatch stays visible
in details for review and may represent another legitimate alternate title.
Neither kind of title match independently verifies identity.
YouTrack may request confirmation for the POST through its Host API even though
this particular endpoint is intended to be read-only.

Provider responses and poster images are not independent verification of
catalog accuracy or personal subscription entitlement. Source availability may
be unknown or partial. The widget displays TMDB and JustWatch attribution and
retains an earlier complete in-memory provider observation if a later check is
incomplete. A failure does not replace a prior successful result.

A JSON response's `Cache-Control: no-store` header, if set, applies to the JSON
response. It does **not** establish how the browser or its caches handle the
separately requested poster image. Image caching and applicable source terms
must be verified separately before treating this as a production integration.

Run the deterministic, fictional-only checks without network access:

```sh
node docs/research/tracker-poc/ui/youtrack_tmdb_check.mjs
node docs/research/tracker-poc/ui/youtrack_ui_check.mjs
```
