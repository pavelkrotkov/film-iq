# Synthetic Movary watched snapshot handler

`movary.js` is a YouTrack app handler that can import a caller-supplied,
source-tagged watched snapshot into the **current user's** `filmMovarySnapshot`
extension property. It does not connect to or modify Movary and does not alter
editable preferences. It has been installed in the local YouTrack instance; a
fictional single-user test and anonymous-denial checks passed, and the local
administrator's 27-film snapshot was imported and read back. A later guarded
update migrated the `FILMREAL` snapshot to mixed v2: all 27 issue/event histories
were preserved, with 16 ID-bound and 11 unbound. Independent-user isolation
and full recovery remain unverified.

The global handler offers `GET movary/watched?project=FILMPOC` and
`POST movary/import`. Both require an explicit `FILMPOC` or `FILMREAL` project.
The POST body must have this shape (the example is fictional):

```json
{
  "version": "youtrack-poc-movary-watched-v2",
  "source": "Movary",
  "complete": true,
  "observed_at": "2026-11-05T12:00:00+00:00",
  "project": "FILMPOC",
  "films": {
    "FILMPOC-1": {
      "watched": true,
      "tmdb_id": 42,
      "played_watch_dates": [{"date": null, "plays": 2}],
      "history_export_dates": [null, "2026-01-05", "2026-01-05"]
    }
  }
}
```

The v2 migration importer starts with the existing v1 issue/event records. It
binds an ID only when the complete same-observation TMDb-keyed source and the
existing snapshot each contain exactly one identical ordered event fingerprint,
and the issue's current supplied ID agrees. A fingerprint includes the watched
flag, every play event and every export date, including repeats and unknown dates.
The full fingerprint multisets must first match or migration stops without a
write. Ambiguous or current-ID-disagreeing records retain all events with
`tmdb_id: null`.
The UI displays watched history and applies watched filters only while that ID
still matches the issue's current supplied ID. A match does not independently
verify the film identity. Legacy v1 entries lack this binding and remain stored,
but the candidate UI reports their watched status as unknown until a mapping is
reviewed and reimported. The handler reads both formats and never changes stored
data during GET. The mixed-v2 candidate has been installed in the local app.
V1 records contain no TMDb IDs. A unique fingerprint match is supporting evidence
within these snapshots, not independent proof of historical identity. Coincidental
events or earlier edits can still misidentify a film. Ambiguous records are not
bound. The migration requires complete input, a full current issue listing and
the same source observation; it is not a general importer for later refreshes or
new users. Fictional tests alone do not verify the real migration.

The importer must independently establish that its source refresh is complete;
the handler only checks the supplied `complete` assertion. It validates all
rows, requires a reported FILMPOC/FILMREAL issue visible to the caller for
every entry, and checks each non-null v2 TMDb ID against the current issue field, then
performs one property write. An invalid, inaccessible, mismatched, or
wrong-project entry rejects the whole import. No ratings, notes or watchlist
fields are accepted. An import replaces that user's previous snapshot for the
specified project and preserves snapshots for other projects; it does not change
the underlying Movary source or personal preference data. An older `observed_at`
is rejected with HTTP 409 for the same project. Equal timestamps are accepted
only if all issue IDs and event values match, and an existing v2 identity remains
unchanged. The handler also rejects replacement if any existing entry is no
longer visible to the caller; it does not silently discard hidden entries. Both
projects share one per-user property, so concurrent
imports and transaction conflict handling still require live verification; the
guard has only been checked sequentially.

Before replacing a snapshot from the same source observation, both the importer
and handler compare issue IDs, event values and existing bound IDs to the proposed
v2 snapshot; a difference stops the import. GET filters out issues the caller
cannot see, so the importer comparison alone cannot prove completeness. The
handler separately checks the entire stored project snapshot and rejects a
replacement containing inaccessible old entries. Inspect the current mapping,
visibility and an owner-controlled recovery path before migrating real data.
The handler has fictional compatibility and rollback tests; the real `FILMREAL`
migration was separately checked by readback. A new import replaces the selected
project's snapshot; it is not a merge or backup.

An older UI ignores the v2 binding and can still show stale watched history after
an ID change, so deploy the matching UI with the handler. An older handler
cannot read v2 entries. Updating the app while retaining the
same extension property is distinct from removing the app; removal deletes its
app-owned data. Before any v2 reimport, establish a tested restoration of the
old property and compatible app version. In particular, downgrading the handler
after v2 is stored can make the watched endpoint fail, so restore the previous
v1 data before downgrade. The candidate's explicit `POST movary/restore-legacy`
accepts only `{"project":"FILMPOC"}` or `{"project":"FILMREAL"}` and converts
that user's current v2 project snapshot to v1 by removing only TMDb bindings;
all issue keys, dates, play counts and observation time remain unchanged. It
rejects unavailable entries, preserves other projects, and a retry is a no-op.
Restore every v2 project before downgrading, since the old handler cannot parse
any v2 project in the property. This converts the current snapshot, not a backup
of an older observation. The candidate has passed offline and isolated live
fictional tests, including mixed bound/unbound entries and a v1 rollback. Those
tests do not verify recovery of the real app or its data. The real snapshot was
migrated but has not been rolled back.

## Real migration and rollback procedure

The guarded local `FILMREAL` migration has been completed once. Its readback
preserved all **27 issue/event histories**, with **16 ID-bound and 11 unbound**;
a subsequent read-only preview again returned 27 entries and 16 bindings. The
other project's watched projection, visible preferences, settings, usages and
attachments were unchanged in the checked before/after observations. These
counts describe this input, not verified identities or evidence that a later
snapshot is unchanged. The v1 issue activity inspected so far does not record
initial TMDb field values, so it does not independently prove the original
issue-to-film bindings.

Owner-only pre-migration v1 projections were retained for both app projects.
They are visibility-filtered API results, not complete raw extension-property
backups. Full app-property or server recovery remains unverified. The following
steps record the method and precautions for any future operation; they are not
an instruction to rerun the migration now.

1. Establish a tested, owner-controlled recovery path before changing the app or
   snapshot. Capture owner-only pre-migration snapshots for **every app project**
   (`FILMREAL` and `FILMPOC`) under the ignored project-private cache, including
   each project's availability state, issue keys, observation time and all
   event arrays returned. Keep personal data and credentials out of Git and
   logs. Record and recheck hashes and counts without printing the contents.
2. The app GET is filtered by the current user's issue visibility and omits the
   underlying property wrapper; it cannot prove an export is complete or capture
   an unscoped `legacy_empty` snapshot. An owner-only filtered export or hash
   alone is not a complete backup. The candidate handler checks the entire
   stored target project and refuses replacement or rollback if an existing
   issue is inaccessible; its conversion preserves other projects and the
   unscoped legacy value. A consistent full YouTrack backup adds protection but
   its restoration has not been verified here. The live fictional rollback test
   proves v2-to-v1 conversion for the isolated fixture app, not a full-server
   restore or recovery of the real app after deletion or database loss.
3. Confirm the original source sidecar is complete, its refresh timestamp matches
   the v1 observation, and the current YouTrack issue listing is complete and
   unambiguous. From the worktree, run the read-only preflight:

   ```sh
   UV_CACHE_DIR="$PWD/.cache/uv" uv run python docs/research/tracker-poc/youtrack_movary_import.py
   ```

   The importer compares the full multisets of ordered watched-event fingerprints
   before proposing any bindings. A proposed ID's fingerprint must occur exactly
   once in the source and once in v1 and agree with the current issue ID.
   A multiset, observation, completeness or mapping error stops the preflight.
   Duplicate fingerprints and ID disagreements remain unbound. Reassess changed
   counts or observations; never treat a unique fingerprint as independent film
   identity verification. GET visibility filtering still means the server-side
   check of the full stored snapshot is required before a write.
4. With the project snapshots captured and visibility checked, update the existing app and its
   UI together while retaining the same app and extension-property identifiers;
   do not remove the app or property. Confirm that the candidate and its
   read-only preflight are the intended versions. Only then run the same importer
   with `--apply`. The handler checks every existing entry's visibility, the
   complete stored same-observation event set, and every non-null ID before its
   single property write. Do not run concurrent imports. The 11 entries in the
   observed migration remain stored but have unknown watched status in the UI;
   an unbound entry is not evidence the film was unwatched.
5. Read back both projects and compare issue keys, all ordered play/export events
   including repeats and unknown dates, observation times and unbound counts with
   their protected pre-migration snapshots. Confirm unrelated app preferences
   and other projects remain intact. A successful HTTP response or matching
   aggregate count alone is insufficient. Preserve the pre-migration projections.

For rollback, keep the compatible candidate handler installed. Call its
`POST extensionEndpoints/filmiq-poc/movary/restore-legacy` for each v2 project
with only its project key in the JSON body. The authenticated current user's
stored v2 snapshot supplies the events; the endpoint refuses unavailable
entries, strips bindings and preserves the current issue/event mappings and
other projects. Compare the resulting v1 data with the protected snapshots and
confirm every project has been restored before reverting the handler and UI. An
`already-legacy` response is a no-op. If observations changed after migration,
this conversion does not restore an earlier observation; recovery of one requires
a separately established recovery procedure. Never uninstall
the app to roll back: doing so deletes its extension properties.

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
