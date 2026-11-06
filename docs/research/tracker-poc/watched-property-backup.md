# Full watched-property backup

The installed POC app provides current-user `GET movary/property-export` and
`POST movary/property-restore` endpoints. Export validates the entire stored
watched property, including all projects and unscoped legacy-empty data, and
refuses to return it if any referenced current or historical issue is not
visible to the caller. Its response is marked `Cache-Control: no-store`. It
contains private watched history and the caller's Hub identity; never print it,
commit it, or put it in a public report.

The project-local CLI writes a new mode-0600 backup inside an owner-only
directory. It does not overwrite an existing file. Restore requires both an
earlier backup and a separately exported expected-current property. Preview is
the default; `--apply` asks the app to compare the exact current property with
that expected export, validate both complete properties and their referenced
issues, and then restore the backup in one property write. The endpoint only
accesses the authenticated user's property and rejects a different backup
owner. It distinguishes absent storage from an explicit empty string.

Preview checks the file envelopes, owner and exact current export; it does not
validate every issue in the backup. The server checks the complete backup and
its visibility when applying. Stop other writers for export/update/restore:
the exact comparison rejects changes made before it, but concurrent
extension-property conflict handling has not been proven to be an atomic
compare-and-swap. If an apply or readback is unconfirmed, inspect the current
property with a fresh export before deciding what to do; do not blindly retry.

For the configured POC, use new file names in the existing private directory:

```sh
.venv/bin/python docs/research/tracker-poc/youtrack_watched_property_backup.py export .cache/tracker-poc/private/watched-before.json
```

After a later update, export the expected current state to a different new
file. To inspect and then deliberately restore the earlier property:

```sh
.venv/bin/python docs/research/tracker-poc/youtrack_watched_property_backup.py export .cache/tracker-poc/private/watched-current.json
.venv/bin/python docs/research/tracker-poc/youtrack_watched_property_backup.py restore .cache/tracker-poc/private/watched-before.json --expected .cache/tracker-poc/private/watched-current.json
.venv/bin/python docs/research/tracker-poc/youtrack_watched_property_backup.py restore .cache/tracker-poc/private/watched-before.json --expected .cache/tracker-poc/private/watched-current.json --apply
```

This is a full *watched-property* export, not a server/database backup or a
backup of editable preferences. It cannot recover data after app removal or
database loss until that broader recovery has been demonstrated. Restore the
property while a compatible handler is installed. A v3 property with historical
entries cannot be read by an older handler; `restore-legacy` refuses to discard
that history. Even a v3-to-v1 conversion with no history drops identity bindings.
All projects in the property must be compatible before downgrading app code.

Before the real v3 refresh, a validated exact raw-property export was saved in
the owner-only project cache. The refresh wrote once and a second full export
confirmed the expected property by semantic JSON comparison, preserving other
projects and legacy-empty state. This provides a property-level recovery point;
real-data restoration and full server or app-removal recovery remain untested.
The earlier project-specific pre-update projections were visibility-filtered
and were not a complete property backup. The refresh and any restore require a
single writer; concurrent atomic compare-and-swap was not verified.

Fictional offline tests cover v2/v3 multi-project data, unscoped legacy-empty
state, hidden current and historical issues, different owners, exact-state
conflicts, absence versus empty storage, and CLI backup/restore. A separate live
FILMPOC-only app with a different ID and property verified the actual Hub
`ringId`, no-store headers, null property writes, v2/v3 exact restoration and
stale-expected rejection; both real watched projections, visible preferences,
and the real apps' settings/usages remained unchanged. This live check did not
exercise multiple projects, concurrent writers or recovery after app deletion.

```sh
node docs/research/tracker-poc/youtrack-app/tests/watched_property_backup_check.cjs
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python docs/research/tracker-poc/youtrack_watched_property_backup_check.py
```
