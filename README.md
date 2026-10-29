# film-iq

**An open-source, evidence-driven film discovery and streaming-planning companion to [Movary](https://github.com/leepeuker/movary).**

**Status:** architecture approved for a proof of concept; implementation and data-provider selections are not yet validated.

film-iq connects critics' lists, polls, festivals, awards, film identity, personal viewing history and US viewing availability. It explains **why a film matters**, distinguishes critical recognition from predicted personal enjoyment, and proposes realistic viewing bundles and optional monthly streaming-service choices. It is not another watch-history application.

## Start here

- [plan.md](plan.md) — complete product and engineering plan, acceptance criteria, research agenda and decision gates.
- [Architecture Decision Records](docs/adr/README.md) — concise accepted and provisional decisions.
- [GitHub Issues](https://github.com/pavelkrotkov/film-iq/issues) — three epics: POC, source exploration, and final implementation.
- [AGENTS.md](AGENTS.md) — contributor and coding-agent workflow.

## Architecture at a glance

Sources → validated, versioned evidence → SQLite → critical and personal scoring → availability offers → monthly plan.

Movary remains authoritative for watched films, dates, personal ratings and explicit watchlist entries. The companion reads that data and writes only **user-approved** watchlist additions. TMDB IDs are operational movie identity, not substitutes for preserved raw source observations.

Initial implementation: Python 3.12+, SQLite on local storage, CLI and reports; optional HTTP service later. HTTP parsing first; Crawl4AI, LangExtract and dlt only after measurements. TMDB/JustWatch is the availability baseline; compare Movie of the Night on specialty-film coverage and plan entitlement before adoption. Avoid graph databases, vector indexes, microservices and a second tracking UI without evidence.

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

CI validates lint, formatting, types, tests, GitHub workflows and dependencies. External API keys are not required for the seeded smoke tests. Future integration tests must use opt-in credentials and redistributable fixtures.

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
This check requires real credentials and has not yet been verified live.

## Project boundaries

- Worldwide film discovery, including shorts, animation, experimental work and documentaries.
- US viewing offers and an initially single-user 5–8-film/month planning capacity.
- No automatic subscription transactions, proprietary dataset mirroring, or unapproved bulk Movary watchlist changes.
- All findings and forecast outputs must distinguish verified observations, assumptions and unresolved hypotheses.

MIT for this repository's original code; source data and adapted OSS components retain their own terms and attribution.

