# Synthetic Movary watched snapshot handler

`movary.js` is a YouTrack app handler that can import a caller-supplied,
source-tagged watched snapshot into the **current user's** `filmMovarySnapshot`
extension property. It does not connect to or modify Movary and does not alter
editable preferences. It has only been tested with synthetic data in a Node
harness; user isolation, permissions, app installation, and persistence have
not yet been verified in a running YouTrack instance.

The global handler offers `GET movary/watched` and `POST movary/import`.
The POST body must have this shape (the example is fictional):

```json
{
  "version": "youtrack-poc-movary-watched-v1",
  "source": "Movary",
  "complete": true,
  "observed_at": "2026-11-05T12:00:00+00:00",
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
fields are accepted. An import replaces that user's previous imported snapshot;
it does not change the underlying Movary source or personal preference data.

GET returns only the caller's currently visible mapped issues. It preserves
unknown dates and repeated observations; absence of a film is **unknown**, not
proof it was unwatched. GET rechecks issue visibility, so losing access removes
that film from subsequent responses. The handler cannot independently prove
that submitted data actually came from Movary: provenance is supplied by the
calling importer, whose identity, completeness and authorization need live
verification before using personal data.

YouTrack app removal deletes extension-property values. Deleting or renaming a
property in an app reimport also deletes that property's old values. Backup,
retention, safe updates and production access control are not designed yet.
See [JetBrains' extension property documentation](https://www.jetbrains.com/help/youtrack/devportal/apps-extension-properties.html).

```sh
node docs/research/tracker-poc/youtrack-app/tests/movary_check.cjs
```
