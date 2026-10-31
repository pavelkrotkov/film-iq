# Agent and contributor guide — film-iq

Adapted from the general-purpose engineering practices in [pavelkrotkov/utils](https://github.com/pavelkrotkov/utils/blob/main/AGENTS.md); intentionally omits its PDF, audio, TIDAL, Swift/macOS and other project-specific instructions.

## Read before changing code

- `plan.md` is the authoritative product and phased engineering reference.
- `docs/adr/` records accepted decisions and decisions gated on POC evidence; do not quietly turn hypotheses into final commitments.
- Consult the relevant open epic and acceptance tests before expanding scope.
- Movary owns personal watched history, ratings, and intentional watchlist. Never write its underlying DB directly.
- Personal ratings, merit comments, viewing schedules and budgets are optional user inputs, never development, deployment or release prerequisites. Do not ask the user to enter or edit them to satisfy acceptance; missing values remain unknown.
- Reuse existing OSS and built-in facilities before creating new infrastructure; document licensing and retention constraints.

## Engineering approach

- Prefer the smallest complete vertical slice and atomic, reviewable commits. Do not mix refactors with unrelated features.
- **Before adding complexity for a speculative or vanishingly unlikely race or security edge case, explain the concrete failure mode, likelihood, and complexity cost to the user and get their buy-in. Do not silently expand scope for theoretical robustness.**
- Do not claim quality, identity precision, streaming availability, personal entitlement, or user satisfaction has been verified until tested.
- No silent truncation of list extraction; no invented film matches; no negative availability event from a failed or partial request.
- A source's missing response is *unknown*, never automatically “not present”.
- Preserve source provenance, correction history and the distinction between independent and derivative critical evidence.
- Changes to personal watchlist require explicit approval and a dry-run preview.
- No paywalled source copies, streaming catalog dumps, credentials or personal ratings committed to Git.

## Python development

- Python 3.12+; use `uv` for environment and execution (`uv sync --dev` and `uv run`).
- Use `ruff check .`, `ruff format --check .`, `ty check .` and `pytest` before publishing a PR.
- Prefer readable typed modules, explicit errors, bounded retries, UTC timestamps and deterministic fixtures.
- Stdlib before third-party imports. Functions snake_case, classes PascalCase, constants UPPER_SNAKE_CASE. Use `pathlib.Path` for local paths.
- Avoid speculative dependencies; document necessity in the corresponding issue and ADR when material.
- New source adapters must define input/rights, validation, lineage, error handling, completeness checks and fixture tests.
- Tests must exercise idempotence, correct rank/tie semantics, source lineage, uncertain film matches, entitlement uncertainty and failed API response handling when those features are implemented.
- Use environment variables or locally ignored config for secrets. Integrations requiring credentials are opt-in in CI.

## Workflow

1. Start from current `main` in a separate branch and worktree for implementation tasks; one issue or coherent change per PR.
2. Open a draft PR early; include scope, linked issue, tests, evidence and any impact on ADRs.
   For partial deliveries, use `Refs #N` or `Related #N` in PR text and commits. GitHub recognizes issue-closing keywords even inside negated sentences, so avoid those combinations. Inspect `closingIssuesReferences` after editing the PR and again before merge; close an issue manually only when its acceptance evidence is complete.
3. Follow `utils`' review discipline: allow bot reviews to arrive, address or evidence-based rebut every finding, and run another review cycle after corrections when available.
4. Do not merge with red/unverified required CI or unresolved review threads.
5. If a green CI missed a defect, add a regression assertion.
6. Avoid direct edits to `main` after the initial repository bootstrap. No unattended automatic merging of dependency updates until the CI and threat model have been checked.

The initial repository seed is a one-time bootstrap exception to the normal PR workflow.

## Agent skills

### Issue tracker

Issues and specifications live in `pavelkrotkov/film-iq` GitHub Issues.
See `docs/agents/issue-tracker.md`.

