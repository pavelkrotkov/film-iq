# B4: remaining dated observations

Issue #14 and Epic #2 require three genuinely separated observation dates.
Oct 30 is date one; repeated requests on that date do not advance the count.
The two later planned passes are **2026-10-31 and 2026-11-01 at 10:00 local
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

The two native macOS calendar jobs now run from the project root on `main`,
using installed Python 3.12 and the existing local `.env`. They have no worktree
or worktree-virtual-environment dependency. Their dates, provider order, request
bound and UTC guard are unchanged. Both replacement commands passed early-date
checks, and a full non-live run produced 120 observations with zero requests.

Private evidence was consolidated with user approval under
`.cache/research-evidence/<worktree-name>/<original-relative-path>`. The local
`index.json` maps original paths to verified SHA-256 copies. Current input and
outputs are relative to the project root:

- Accepted cohort: `.cache/research-evidence/b14-live-comparison/.cache/motn/accepted-paired-manifest-20261030.json`.
- Job configurations, logs and dated results: `.cache/research-evidence/b14-dated-runs/.cache/dated-runs/`.

The active configurations have `main-` filename prefixes; copied original
configurations/receipts remain historical evidence. Both native registrations
were re-read with zero runs and no worktree paths. GitHub issues, `plan.md` and
the linked reports carry the public findings; no private provider output or
credential enters Git. Old worktrees can be removed while preserving their
branches and the copied evidence. Registration is not future measurement.

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

## Date-two execution inspected — 2026-10-31

The [second dated report](comparison-20261031.md) verifies the Oct31 job completed
one run with exit 0: 120 observations/requests, all HTTP 200, from 14:00:00 to
14:00:11 UTC using the unchanged accepted manifest. TMDB has 53 complete US
responses/seven unknown; native has 49 complete/11 unknown. Complete-pair native
source opportunity sets changed for five film keys (nine present/two absent),
while 12 keys changed in the broader detail comparison. These are source claims,
not independently confirmed removals or measured change latency. No quota headers
were returned. Native source rows changed 274→284; variant rows and deduplicated
opportunities are different units.

At 14:58 UTC, the Nov1 job still had zero runs and no result file. Date three and
final reviewed B4/B8 adjudication remain pending. Jobs, cohort, credentials and
source captures were not changed by this inspection; public discovery still
needs no consumer sign-in. Original rights/deletion deadlines remain in force.
