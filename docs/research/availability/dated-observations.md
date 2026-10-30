# B4: remaining dated observations

Issue #14 and Epic #2 require three genuinely separated observation dates.
Oct 30 is date one; repeated requests on that date do not advance the count.
The next two planned passes are **2026-10-31 and 2026-11-01 at 10:00 local
America/New_York time** (14:00 and 15:00 UTC respectively across the DST change).
They reuse the accepted both-ID manifest with SHA-256
`303cd59ff2996571492a7aaee032c26fd7552673e234951295c625a515a0aa12`.

## Execution

Use the existing paired CLI with `--on-date YYYY-MM-DD`. The optional guard
rejects any other UTC date **before cohort access or HTTP requests**. Output
still uses exclusive creation, so an existing observation cannot be overwritten.
This avoids annual calendar recurrence or an early manual trigger becoming an
extra study pass. No retries, new service, dependency or credential upload is
needed. Existing unknown/error handling and no-removal behavior are unchanged.

Two local macOS launchd calendar configurations are prepared under this
worktree's ignored `.cache/dated-runs/`. They call the installed `uv` with the
existing project `.env`, current source path and existing Python interpreter.
The frozen local manifest stays in the earlier observation worktree. Logs and
normalized observations stay under `.cache/dated-runs/`; no catalog dump, token
or actual offer fixture enters Git. The jobs will be loaded and their native
registration verified only after the PR's review and CI pass. Preparation is
not registration or execution; the issue comment records verified installation.

Each job attempts at most 120 requests (60 per provider), with no extra discovery
queries. Two planned passes add at most 240 requests. Missing credentials, failed
responses and missing country data stay unknown. Their presence does not prove
quota balance, full catalog completeness, exact-tier access or a confirmed removal.
Applicable [provider rights](rights-20261030.md) remain part of the decision gate;
TMDB study cache has a conservative 2027-04-30 deadline. No paid plan or consumer
streaming login is required.

## Completion checks

Registration is a plan to collect evidence, not evidence from the future. The
Mac must be available with network access; successful execution is not guaranteed.
A missed date must be rescheduled for another genuinely later date. An annually
recurring calendar trigger on a wrong UTC date exits before requests. No
automatic issue closure or merge is installed.

After each pass, inspect native job state/logs, the actual UTC timestamps,
manifest hash, per-provider counts, failures and quota headers. Compare source
assertions only where both observations are complete; investigate differences
with bounded public first-party checks. Missing data is unknown, never a removal.
Where no independently timed offer change occurs, change latency remains
inconclusive rather than zero. Keep tier and account uncertainty explicit for
pre-subscription discovery. Publish the dated summary through the ordinary
reviewed PR workflow, then adjudicate #14 and the final Gate B. Unload the two
local jobs after the experiment; preserve source evidence and project files.
