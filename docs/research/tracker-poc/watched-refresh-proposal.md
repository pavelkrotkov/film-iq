# Newer Movary watched observations: offline proposal

This is an undeployed candidate, not a scheduled job or completed migration.
`youtrack_watched_refresh_proposal.py` builds a pure preview;
`youtrack_watched_refresh.py` adds a dry-run-first importer and an explicit
`--apply` path for the candidate v3 app's `/refresh` endpoint. The currently
deployed v2 importer remains a same-observation migration only. No real
snapshot, YouTrack record, Movary data, browser session or network service is
used by the fictional tests.

The proposal consumes a newer successful Movary snapshot and its matching
non-stale status, three API collections and a history export. It reuses the
existing snapshot mapping, derives watched membership from the API and export
provenance, and stops if the derived and reported watched sets disagree. It
requires every watched ID to match exactly one current FILMREAL issue ID and
stops on missing, duplicate or malformed identities, unresolved history,
unavailable prior issues or non-increasing observation times. Source IDs are
supplied mappings, not independently verified film identities.

Current source events appear under the new observation time. Older unbound
entries and prior bound entries that changed, disappeared or no longer match
their issue are retained separately with their original issue, timestamp and
events. Current and historical evidence can therefore coexist for one issue;
historical unbound events do not establish that issue's current watched status.
Existing historical entries survive another proposal. A complete source can
still reflect edits between its API and export reads, and a manually supplied
CSV's completeness is operator-asserted, as described in the
[personal refresh documentation](../../usage/personal-refresh.md).

The candidate app stores current and historical entries in a v3 snapshot. Its
handler independently validates the full stored property and checks access to
all its current and historical issues before a write; the visibility-filtered
GET alone cannot establish that completeness. It derives old history from the
stored property instead of accepting it from the client, rejects newer imports
that bypass `/refresh`, and makes an identical v3 retry a no-op. The importer
validates source provenance, but the handler itself can only validate the
caller's completeness assertion; it cannot independently verify Movary's export.

Old handlers cannot read v3 data. The candidate `restore-legacy` endpoint
rejects conversion when historical entries exist, because v1 cannot represent
them. If history is empty, conversion is possible but drops identity bindings;
it is not a lossless rollback. Every stored project must be compatible before
downgrading the handler, and removing or renaming an app property can delete
app-owned data. The handler passed a live test in a separate fictional YouTrack
app, including mixed v2-to-v3 refresh, original history timestamps, retry and
refusal of a lossy downgrade. Hidden-existing-entry rejection remains an
offline check. This candidate has not been installed in FilmIQ or applied to
real data.

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python docs/research/tracker-poc/youtrack_watched_refresh_proposal_check.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python docs/research/tracker-poc/youtrack_watched_refresh_vertical_check.py
node docs/research/tracker-poc/youtrack-app/tests/movary_check.cjs
```

The fictional check covers a prior unbound entry alongside a new direct-ID
observation for the same issue, changed and removed mappings, repeat refresh,
API-history-only and CSV-only films, inconsistent source membership, stale or
incomplete input, duplicate and missing issue IDs, malformed dates, and input
preservation. The vertical check connects the actual Python importer to the
actual JavaScript handler in a fictional mock context: preview, apply, retry,
incomplete-source rejection and hidden-stored-entry rejection. It does not
exercise a live Movary refresh or the real FilmIQ app update.
