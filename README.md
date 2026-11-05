# film-iq

Personal ratings, merit comments and viewing plans are optional. Discovery and
core deployment work without them; the planner accepts private budget/time inputs
only when voluntarily invoked. No personal entries, edits or actual spending
decision are required to finish development or release.

**An open-source, evidence-driven film discovery and streaming-planning companion to [Movary](https://github.com/leepeuker/movary).**

**Status:** The recommendation UI provides browsing, original-source evidence, a persistent local shortlist and deliberate Movary actions. Private HTTPS deployment has passed browser/recovery checks; its final review is tracked in [PR #104](https://github.com/pavelkrotkov/film-iq/pull/104). Production streaming-provider adoption remains separate.

film-iq connects critics' lists, polls, festivals, awards, film identity, personal viewing history and US viewing availability. It explains **why a film matters**, distinguishes critical recognition from optional personal judgments, and proposes realistic viewing bundles and optional monthly streaming-service choices. FilmIQ is the recommendation interface; Movary remains the personal-history backend.

## Start here

- [plan.md](plan.md) — complete product and engineering plan, acceptance criteria, research agenda and decision gates.
- [Architecture Decision Records](docs/adr/README.md) — concise accepted and provisional decisions.
- [GitHub Issues](https://github.com/pavelkrotkov/film-iq/issues) — three epics: POC, source exploration, and final implementation.
- [AGENTS.md](AGENTS.md) — contributor and coding-agent workflow.

## Browse recommendations

The [recommendation website](docs/usage/recommendation-ui.md) now provides
searchable film cards and original-evidence details using the same inputs:

```sh
uv run film-iq serve --database path/to/evidence.db --cohort path/to/accepted-cohort.json
```

Open `http://127.0.0.1:8770/`. Personal history and reviewed display metadata are
optional. Save/Dismiss/Restore keeps a FilmIQ shortlist. Optional Movary controls
preview and explicitly confirm watchlist additions or a dated watch; rating edits
use the native Movary page. Read-only refresh brings those values back. See the
[website guide](docs/usage/recommendation-ui.md) for configuration and the private
HTTPS deployment. Its Mac host must remain awake and logged in; process restart
supervision does not imply automatic login/reboot startup.

## Read a discovery report

Use selected accepted cohort previews and an existing private snapshot:

```sh
uv run film-iq discover --cohort path/to/accepted-cohort.json --database path/to/evidence.db --snapshot path/to/private/snapshot.json --catalog path/to/reviewed-catalog.json
```

Repeat `--cohort` for more editions. `--catalog` is optional reviewed display
metadata; omit `--snapshot` to leave personal/watched state unknown. History and
both scores may be absent; a fresh complete history snapshot supports watched
exclusion even with no ratings. No budget or schedule is requested. See the
[discovery workflow](docs/usage/discovery-report.md) and [optional planner](docs/usage/planning-report.md).

## Architecture at a glance

Sources → validated, versioned evidence → SQLite → public recognition → discovery/report.
Movary history supports watched exclusion; personal ratings and planning are optional.
Availability integration retains its separate production-provider gate.

Movary remains authoritative for watched films, dates, personal ratings and explicit watchlist entries. FilmIQ reads that data and writes only explicitly previewed and confirmed watchlist additions or watch dates through supported APIs. TMDB IDs are operational movie identity, not substitutes for preserved raw source observations.

Implementation: Python 3.12+, local SQLite, CLI/reports and a server-rendered recommendation UI ([build epic](https://github.com/pavelkrotkov/film-iq/issues/98)). HTTP parsing first; Crawl4AI, LangExtract and dlt only after measurements. TMDB/JustWatch is the availability baseline; compare Movie of the Night on specialty-film coverage and plan entitlement before adoption. Avoid graph databases, vector indexes, microservices and speculative frontend infrastructure.

## Development

Once dependencies are installed:

```bash
uv sync --dev
uv run ruff check .
uv run ruff format --check .
uv run ty check .
uv run pytest
uv run film-iq --version
```

CI validates lint, formatting, types, tests, GitHub workflows and dependencies. External API keys are not required for credential-free tests. Live integration checks are opt-in.

### POC commands

```sh
uv run film-iq status
uv run film-iq report --database path/to/evidence.db --inputs path/to/report-inputs.json
uv run film-iq sync --title "Bicycle Thieves" --tmdb-id 5156
```

The report defaults to Markdown; `--format json` returns structured output.
The sync command above is an offline preview. See [report inputs](docs/poc-report.md)
and the [approved-write boundary](docs/a7-write-boundary.md) before live execution.

### Opt-in Movary integration

For an authorized test account, set `MOVARY_INTEGRATION=1`, `MOVARY_URL`,
`MOVARY_USERNAME`, and `MOVARY_TOKEN`. Set `MOVARY_VERSION_COMMAND` to a JSON
array of arguments for a command that prints the installed version, and
`MOVARY_EXPECTED_VERSION` to its exact expected stdout. Set `MOVARY_EXPORT_COMMAND`
to a JSON argument array ending with `user:export:ratings` and the user ID;
the test appends the export filename. Set `MOVARY_RATED_ONLY_TMDB_ID` to a
known rated film with no played entry in that account. Set `MOVARY_SNAPSHOT_DIR`
to a private existing directory visible at the same path to the export command.
Then run `uv run pytest -s tests/test_movary_integration.py::test_live_movary`. The test
creates and removes a temporary snapshot there. Commands run without a shell;
wrappers must expose the installed version and make the export path visible.
This dedicated nonempty rated-only check remains unrun on the empty POC ratings
account. Real API reads, atomic empty ratings export/replay and an approved
watchlist addition/readback/retry are recorded in [the live validation](docs/a7-live-validation.md).

## SQLite migration and recovery

Before migrating an existing database, stop writers and use SQLite's online backup API
to create a separate backup on local storage. Copy that backup to the chosen backup
location together with the application version and configuration; protect any secrets
and retained source data according to their policies. Do not copy only the main database
file while WAL is active: committed changes may still be in the WAL.

For example, with Python and paths chosen for your installation:

```python
import sqlite3

with sqlite3.connect("film-iq.db") as source, sqlite3.connect("film-iq-before.db") as backup:
    source.backup(backup)
```

After a migration failure, stop all database connections. Preserve the failed database
for diagnosis, then restore the backup to a fresh local path using the same backup API
(with the backup as source). Open the restored database with the previous application
version, check `PRAGMA integrity_check` and `PRAGMA user_version`, and verify expected
records before resuming. Migrations have no automatic downgrade; restoring a backup
discards changes made after it was taken. Test this procedure with an actual backup
before relying on it. Keep the live WAL database on local storage, not a network share.

Earlier draft version-1 databases used a different schema under the same version
number. Migration rejects that obsolete shape before changing it. Preserve the database
and use its original application version to export or inspect its data; create a fresh
database with the current version and re-import only after reviewing the provenance.
There is no automatic conversion. Version-4 databases with supersession links between
different entries are also rejected; inspect and correct those links with the previous
application version after backing up, then retry migration.

Each extraction revision belongs to one list and document. Select a list's current
accepted revision through `current_extraction`; update that pointer in the same
transaction as acceptance, and query observations through it to avoid counting old
revisions as new endorsements. Historical revisions and their observations remain.

## Project boundaries

- Worldwide film discovery, including shorts, animation, experimental work and documentaries.
- US viewing offers; optional single-user planning uses capacity supplied at invocation, never inferred viewing habits.
- No automatic subscription transactions, proprietary dataset mirroring, or unapproved bulk Movary watchlist changes.
- All findings and forecast outputs must distinguish verified observations, assumptions and unresolved hypotheses.

MIT for this repository's original code; source data and adapted OSS components retain their own terms and attribution.


Local changes can be previewed without external notifications:

```sh
uv run film-iq changes --database path/to/evidence.db --checkpoint path/to/private/changes-seen.json
uv run film-iq changes --database path/to/evidence.db --checkpoint path/to/private/changes-seen.json --format json --output path/to/private/changes.json --ack
```

First use explicitly establishes a baseline instead of announcing the existing
catalog. Preview leaves the checkpoint untouched; `--ack` records opaque event
IDs and accepted revision pointers only, after atomic private output publication
or successful stdout flush. Use one consumer per checkpoint. A failed output is
not acknowledged; failed/partial source requests and expired/denied retention do
not imply disappearance. Reports inherit the underlying sources' original
permissions and retention deadlines; an exported report grants no longer lease.
Provider adoption remains gated separately. No provider polling, personal-state
writes, external delivery or web endpoint is enabled by this command.
