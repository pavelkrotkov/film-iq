# Versioned public-evidence ranking

`independent-priority-rank-v2` preserves independent evidence-group counts and
reciprocal-rank totals separately. These are provisional external critical
recognition components, never personal enjoyment, user artistic merit or a
predicted preference. No weight calibration, award/reception conversion or
absence penalty is introduced.

```python
from film_iq.scoring import score
from film_iq.scoring.policy import ScoringPolicy

policy = ScoringPolicy(
    source_priority=("preferred-original-source", "other-original-source"),
    window_priority=("2023 new releases", "2023 retrospective"),
    excluded_families=("held-out-publisher-family",),
)
results = score(accepted_observations, policy=policy)
```

Declare the policy before inspecting a film's ranks. For repeat support of a
film, lower declared source priority wins, then window priority. Sources absent
from the priority tuple follow the named sources; remaining ties use canonical
source, eligibility, publication and entry/revision provenance. The default
policy is the same canonical ordering, declared by the algorithm, not an
empirically optimal ordering. A window is the supplied eligibility string;
unknown release years and unseen-film exposure are not inferred. Conflicting
ranks for the same ballot/provenance priority require review rather than a
best-rank choice. All original ranks and excluded evidence remain explainable.

`person_id` is an explicitly reviewed stable contributor identifier. Matching
author strings or publisher grouping alone never establishes a person identity.
Known people are deduplicated across source groups; inputs without person IDs
use their previously reviewed independence groups as evidence support units.
Mixed linked/unlinked ballots retain that group dependence while explicit
person links also deduplicate overlapping groups. Missing row-level identities
are never filled in. Conflicting person IDs within one reviewed group require
review before scoring or snapshot insertion.
`independent_count` therefore counts supported evidence groups, **not inferred
independent critics**. `known_person_count` and `unknown_contributor_count`
expose this distinction. The latter counts support units with unknown
contributors, not an estimated number of people. Existing extraction, identity,
evidence-disagreement and prediction uncertainty fields remain separate and
uncalibrated.

Snapshots store both the complete unique evidence inputs and the declared
policy. Policy changes create distinct v2 IDs; identical reruns retain the same
ID. Historical `independent-reciprocal-rank-v1` snapshots replay their original
best-rank numeric policy and retain the old version label; saving their inputs
now produces a distinct v2 snapshot. Unsupported versions fail explicitly.

The current A1 reader carries verified source-family/lineage metadata and C1's
explicit contributor/ballot links. It does not infer `person_id` from `author`;
a derivative original-ballot link excludes a repeated endorsement even if the
publisher list was classified original. Typed award/reception ingestion remains
pending. Both B7 experiments
remain performed but inconclusive. Offline duplicate, tie/unranked,
source-family holdout and snapshot checks demonstrate semantics, not predictive
quality or a completed Gate C.
