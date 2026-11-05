# Synthetic YouTrack preference experiment

This uninstalled, unverified experiment stores a JSON map of readable issue ID
to preference on the current user's `filmPreferences` User extension property.
The `preferences` handler exposes `GET /preference?issue_id=FILMPOC-1`,
`GET /all` (the caller's recorded, currently visible films),
`POST /preview` with `{issue_id, preference}`, and `POST /confirm` with the
exact preview `{issue_id, before, after}`. The only write path uses a distinct
server-stored preview and checks the current value again. A new preview replaces
the user's previous pending preview; replay or stale confirmation is rejected.
When no row exists, the read result is `{recorded: false, preference: null}` and
the preview's `before` is `null`; this state does not mean unwatched or absent
from a watchlist. After a confirmed change, `recorded` is `true`. A caller must
explicitly provide every field of the proposed preference. `watchlist: null`
means unknown even on a recorded row; `watched_at: null` means no timestamp was
recorded and does not independently establish that a film was not watched.
The handler checks the authenticated current user, the FILMPOC or FILMREAL project, and
`issue.isVisibleTo(currentUser)` for every read and write. Input timestamps must
be canonical UTC ISO strings with milliseconds. Watchlist flags are synthetic;
this code never calls Movary.

Per-user extension properties are not sortable or range-queryable in native
issue search, and fetching one issue at a time may be slow; no 1,000-film or
concurrency measurements have been made. We have not established whether
simultaneous updates to different issues on the same user's JSON map conflict or
can overwrite each other. Backups, retention and deletion still need design.
The POC relies on YouTrack's authenticated global endpoints and disabled guest
login, and the authorization behavior has only been tested in a synthetic
JavaScript harness, not in YouTrack or with real user accounts. Do not use real
personal data until live access and isolation tests pass.

Removing the app deletes its extension property data; reimporting an app after
removing or renaming properties also deletes the corresponding values. See
[extension properties](https://www.jetbrains.com/help/youtrack/devportal/apps-extension-properties.html),
[HTTP handlers](https://www.jetbrains.com/help/youtrack/devportal/apps-reference-http-handlers.html),
and [extension-property search limitations](https://www.jetbrains.com/help/youtrack/devportal/apps-faq.html).
