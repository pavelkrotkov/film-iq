# Private Movary personal snapshot (C0a #58)

Run `python -m film_iq.refresh_movary` through `uv run` with `MOVARY_URL`,
`MOVARY_USERNAME` and `MOVARY_TOKEN` in the process environment. It reads all
played/history/watchlist pages; it never calls a write endpoint. Keep the output
inside the project's ignored private `.cache` (or another explicitly selected
private project directory). The atomic JSON and status files are mode 0600;
the parent is created mode 0700 when absent. Existing parent permissions are
not changed.

Provide `--snapshot .cache/personal/snapshot.json` and either `--ratings-csv`
plus `--history-csv`, or `--ratings-command` plus `--history-command`.
Each command option is a JSON argv array executed without a shell and must emit
only the complete CSV to stdout. For the installed 0.82.1 deployment the supported
CLI is `php bin/console.php user:export:ratings 1 php://stdout --silent` and the
analogous `user:export:history` command. A local or SSH wrapper may run these
commands; do not put secrets in argv. Each subprocess has a 300-second timeout.
Failed stderr is suppressed because it can contain private fields.

Explicit CSV files are a lightweight operator-asserted complete-export fallback,
not proof of a live read. Both exact schemas and every row are validated before
publication. The complete JSON replacement includes original CSV rows, original
comments and complete API collections for private provenance; do not attach it
to a PR, logs or a public report. Successful command termination plus schema
validation cannot independently establish that a manually supplied CSV contains
every server row. The source is not transactionally frozen across the API and
CLI reads; concurrent user edits may require another refresh.

The report-facing `films` array has explicit TMDB and nullable Movary IDs,
watched status/dates, watchlist status, nullable `personal_enjoyment`, nullable
`personal_artistic_merit`, `merit_status` and separate rating provenance. Native
ratings CSV supplies enjoyment. Only literal `Artistic merit: N/10` for integer
N from 1 through 10 in History **CLI** comments supplies merit. Duplicate comment/
date assertions from repeated plays are one assertion. Conflicting scores on
any distinct date entries produce `conflict`, never latest/highest selection.
Malformed assertions produce `invalid`; absent assertions produce `unknown`.
Both states have null merit. Missing dates remain null. Rated-only films are
not assumed watched. Missing CSV IDs stay in `unresolved`, without title-based
matching. These personal judgments are never external critical recognition.

The JSON is published only after all five complete reads validate. A failed
refresh preserves the prior successful JSON and writes `snapshot.json.status`
with `stale: true`; consumers must read this status before describing freshness.
A successful replacement reconciles deleted enjoyment ratings and removed/edited
merit comments. Raw CSVs are staged in a private temporary directory under the
snapshot parent, represented in the atomic snapshot and removed afterward.

## Validation boundary — 2026-10-30

Credential-free synthetic tests cover changed/deleted ratings, merit edits,
conflicting date entries, duplicate plays, rated-only films, unknown dates,
identity uncertainty, malformed exports, failed commands and stale replacement.
Pinned Movary 0.82.1 ExportService/ExportWriter source verifies both headers and
the duplicate-per-play behavior; installed read-only CLI help confirms the
history exporter path and arguments. No real personal data has been exported
by this change. Automatic approval review rejected the attempted genuine
read-only acceptance command because implementation authorization did not
specifically authorize exporting/retaining private personal data. Explicit user
approval is required before retrying. Consequently nonempty live history,
real merit readback, live edits/deletions and the 5–15-film acceptance remain
pending; #58 must remain open.

## Authorized live execution follow-up — 2026-10-30

The user explicitly approved the previously blocked read-only operation. The
configured-account API reads and both supported installed CSV exporters completed
successfully, and the private complete snapshot/status were published. A fresh
private discovery report was generated using the matching snapshot generation.
Operational receipts and report files remain under the selected project's ignored
`.cache/epic-c/personal/` and `.cache/epic-c/results/`; no personal records, scores,
comments, identifiers or account-level counts are published here.

This supersedes the authorization/execution blocker above, not the remaining
acceptance requirements. Nonempty genuine enjoyment/merit readback, rated-only
behavior and changed/deleted ratings or merit comments remain unverified live.
No user records were fabricated or modified to manufacture those cases. #58/#25
and the real-user acceptance gate remain open. No watchlist writes, service
purchases, production-provider adoption or B4 job changes occurred.
