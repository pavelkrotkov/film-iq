# Synthetic Movary watched snapshot handler

`movary.js` is a YouTrack app handler that can import a caller-supplied,
source-tagged watched snapshot into the **current user's** `filmMovarySnapshot`
extension property. It does not connect to or modify Movary and does not alter
editable preferences. It has been installed in the local YouTrack instance; a
fictional single-user test and anonymous-denial checks passed, and the local
administrator's 27-film snapshot was imported and read back. Independent-user
isolation and recovery remain unverified.

The global handler offers `GET movary/watched?project=FILMPOC` and
`POST movary/import`. Both require an explicit `FILMPOC` or `FILMREAL` project.
The POST body must have this shape (the example is fictional):

```json
{
  "version": "youtrack-poc-movary-watched-v1",
  "source": "Movary",
  "complete": true,
  "observed_at": "2026-11-05T12:00:00+00:00",
  "project": "FILMPOC",
  "films": {
    "FILMPOC-1": {
      "watched": true,
      "played_watch_dates": [{"date": null, "plays": 2}],
      "history_export_dates": [null, "2026-01-05", "2026-01-05"]
    }
  }
}
```

The importer must independently establish that its source refresh is complete;
the handler only checks the supplied `complete` assertion. It validates all
rows, requires a reported FILMPOC/FILMREAL issue visible to the caller for
every entry, then performs one property write. An invalid, inaccessible, or
wrong-project entry rejects the whole import. No ratings, notes or watchlist
fields are accepted. An import replaces that user's previous snapshot for the
specified project and preserves snapshots for other projects; it does not change
the underlying Movary source or personal preference data. An older `observed_at`
is rejected with HTTP 409 for the same project; equal timestamps are accepted,
including repeat imports. Both projects share one per-user property, so concurrent
imports and transaction conflict handling still require live verification; the
guard has only been checked sequentially.

Legacy snapshots without a project field are read by grouping their existing
issue IDs by project; after a successful import, the grouped snapshots are kept
in the project-scoped format. An empty legacy snapshot has no provable project
identity, so it is retained as unscoped and does not imply any project's status.
Malformed legacy data fails closed and is not overwritten.

GET returns only the caller's currently visible mapped issues. It preserves
unknown dates and repeated observations; absence of a film is **unknown**, not
proof it was unwatched. GET rechecks issue visibility, so losing access removes
that film from subsequent responses. The handler cannot independently prove
that submitted data actually came from Movary: provenance is supplied by the
calling importer, which checks its input before the local import. The handler
itself cannot independently validate that provenance or completeness.

YouTrack app removal deletes extension-property values. Deleting or renaming a
property in an app reimport also deletes that property's old values. Backup,
retention, safe updates and production access control are not designed yet.
See [JetBrains' extension property documentation](https://www.jetbrains.com/help/youtrack/devportal/apps-extension-properties.html).

```sh
node docs/research/tracker-poc/youtrack-app/tests/movary_check.cjs
```
