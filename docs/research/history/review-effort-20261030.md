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
