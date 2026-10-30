# B2 timed review-effort supplement — 2026-10-30

## Protocol frozen before the timed review

This supplement measures one agent performing the manual evidence-review task,
not an automatic resolver and not human labor. It reuses the fourteen-case
sample and the retained search/detail/source receipts from the earlier live
experiment. The reviewer has already seen the earlier 12 accepted / 2 ambiguous
summary and some evidence: this is an unblinded repeat review, not fresh truth,
a training-time benchmark or an independent precision test.

Five timed blocks use the mutually exclusive primary source frames: Cannes
(nine cases), Berlinale (two), Annecy (one), Criterion derivative retrospective
(one), and Film at Lincoln Center (one). Each block starts before reading its
case evidence and ends when written case decisions/rationales are saved. Check
titles/aliases, directors, type/runtime and separately labeled dates; preserve
unknown premiere/publication/local-release fields and material conflicts.
A work-level match never resolves a cut or release-event disagreement. Record
accepted, ambiguous and unknown decisions, changes from the prior audit,
and follow-up actions. Do not change sample.json or its null activation IDs.

UTC and monotonic-clock boundaries are recorded locally. Block intervals include
model reasoning, tool execution and latency, reading and entering decisions;
they exclude initial task/source setup, between-block pauses, report writing,
CI, provider acquisition and earlier audit work. No pauses are subtracted
within blocks. Report aggregate elapsed seconds/minutes by source frame and
period. No per-case timing is inferred from a multi-case block. Human sample
size remains zero and human minutes null; model billing is unmeasured.

The local receipt records input hashes and decisions; the public report publishes
only concise derived findings. No live provider requests, new dependencies,
production resolver changes or provider response redistribution are needed.

## Measured results

The frozen protocol commit is `a066268`. Five blocks ran from
**14:04:56.691527 to 14:05:55.929216 UTC**. Their monotonic-clock intervals sum
to **59.235865 seconds (0.987264 minutes)**. This is observed agent-assisted
manual-task wall time, including tool/model latency, not hands-on human minutes
or an estimate of what a person would need. One agent reviewed fourteen cases;
human review sample size is zero. No new provider requests were made.

| Primary source frame | Cases | Accepted / ambiguous / unknown | Agent-task seconds | Agent-task minutes | Human minutes |
| --- | --- | --- | --- | --- | --- |
| Cannes | 9 | 8 / 1 / 0 | 22.453054 | 0.374218 | null |
| Berlinale | 2 | 2 / 0 / 0 | 11.506131 | 0.191769 | null |
| Annecy | 1 | 1 / 0 / 0 | 8.792553 | 0.146543 | null |
| Criterion derivative retrospective | 1 | 0 / 1 / 0 | 7.102810 | 0.118380 | null |
| Film at Lincoln Center | 1 | 1 / 0 / 0 | 9.381317 | 0.156355 | null |

The sample still has six 2010s, six 2020–2026 and two older retrospective cases.
Timing belongs to primary-source blocks: Cannes and Berlinale each mix periods,
so period-level timing cannot be isolated and remains unmeasured. This is an
explicit boundary of the protocol's requested period reporting; no time is
allocated proportionally to cases. Period counts and the earlier outcomes
remain in the [live report](live-20261030.md).

All fourteen decisions were written with case-specific rationales in the local
receipt: **twelve accepted, two ambiguous, zero unknown**. There were **zero
changes from the prior audit's statuses** and **zero source-field corrections**.
The work performed was evidence comparison and entering a separate decision
log; unchanged decisions do not imply zero review effort. No automatic resolver
ran, and no production accepted ID or frozen sample field was changed.

The two ambiguous cases remain `history-10` (*The Man Who Could Not Remain
Silent*, source production/competition 2024 versus catalog release 2025 and
13/14-minute conflict) and `history-13` (*Jeanne Dielman*, source 1975 label
versus catalog 1976 release). Follow up dated-event/cut context only if activation
is needed; do not force either ID. Accepted work identities preserve the
13/14-minute *All These Creatures* lead, 14/15-minute *The Water Murmurs* source
conflict, *Percebes* seconds-level duration uncertainty, and *No Other Land*'s
US-release/undistributed-list eligibility conflict. Review acceptance never
certifies an exact cut, premiere or local-release eligibility.

## Source taxonomy and research conclusion

Following [B1's source taxonomy](../sources/registry.md), Cannes, Berlinale and
Annecy are festival selection/award evidence; those events are not critic
ballots. Criterion's retrospective is a derivative account of Sight and Sound,
not another independent poll. Film at Lincoln Center's staff retrospective
records a viewing-year selection. Additional Film Comment observations for
*No Other Land* retain their own criteria; they are not extra primary-frame
cases or proof of US eligibility. This reconciles reporting frames without
claiming cross-source population coverage.

The earlier 35-request TMDB experiment and six alias queries remain unchanged:
14/14 selected candidates were returned with usable details; 5/6 selected
aliases retrieved the reviewed work. Those are conditional retrieval results.
Automatic-acceptance coverage is **0/14**, automatic-match precision is
**undefined** (no automatic acceptances), and a missing-catalog rate remains
**unknown** (no confirmed absence assessment). The repeat agent decisions are
not an independent precision answer key. Human effort is also an explicit
inconclusive outcome, rather than a number inferred from agent wall time.

For the initial expansion, prioritize source-linked festival shorts and
translated-title aliases, with a review queue for differing release-event and
runtime contexts; expand older retrospectives next. Keep documentary and
animation strata explicit. Do not select a new resolver, claim general catalog
coverage, or expand automated ingestion before the source-specific rights are
resolved. [ADR 0003](../../adr/0003-film-identifiers.md) and
[ADR 0011](../../adr/0011-cost-rights.md) remain unchanged.

This supplies the performed source-stratified review task and measured agent
cost boundary for #12. It does not establish human labor or make an identity
accuracy claim. B2 can report these bounded findings and inconclusive metrics
without waiting for a positive result; closure remains subject to PR review
and the controller's explicit acceptance of this agent-assisted experiment.

## Receipt and validation

The ignored local receipt is
`.worktrees/b12-review-effort/.cache/review-effort-20261030.json`, SHA-256
`cb9960be5181556613671b1d58f4a5d66892fe4e128bf4bcfcd49a43c365cbaa`.
It records five UTC/monotonic boundaries, all fourteen rationales and input
hashes. The sample, search, detail and prior-audit inputs retain their published
hashes in the [earlier report](live-20261030.md); source-note content is also
hashed in the receipt. Provider facts remain local; no API response body,
credential or publisher text is added to Git. The receipt's creation does not
grant historical-retention rights. The source sample and its null IDs are
unchanged, so later reviewed activation remains separate.


Documentation-only supplement validation: Ruff check and format check, ty and
pytest passed (**340 passed, one opt-in integration skipped**). Radon over all
159 tracked Python files reports maximum CC **8**, minimum MI **50.025032**;
no Python source/test/dependency changed. A local receipt check verified fourteen
unique decisions, five non-overlapping blocks, unchanged prior statuses and the
reported sum. No test is added for prose or to simulate human timing.
