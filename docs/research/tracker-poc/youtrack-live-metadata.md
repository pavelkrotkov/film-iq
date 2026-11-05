# YouTrack live metadata widget experiment

The widget source can request one film, or up to 30 currently displayed and
unattempted films, only after a user action. Requests are sequential and stop
on any failed request or a project/refresh change. This also stops a rate-limited
batch when the Host API does not expose the HTTP status. Failed films are not
automatically retried; an individual film can be retried explicitly. The
response is held in page memory, not written to issue fields or preferences.

This source expects a separately installed and configured issue-scoped handler
at `issues/{issueId}/extensionEndpoints/filmiq-tmdb-live-isolated/metadata/read`.
It sends a POST with an empty JSON body through `host.fetchYouTrack`. The
handler must authenticate the current user, validate issue access, enforce the
authorized film-ID allowlist and keep credentials server-side. The widget checks
that the response ID matches the issue's supplied ID, but this does not prove
that the supplied ID identifies the intended film. The handler and widget are
installed, and direct API checks passed for the approved set; invoking the
handler through the main-menu widget has not yet been verified in a browser.
Grid artwork, provider data and live genre filters require the returned title
to match the issue title after Unicode normalization, case and whitespace
normalization. A mismatch stays visible in details for review and may represent
a legitimate alternate title. A matching title does not verify the identity.
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
