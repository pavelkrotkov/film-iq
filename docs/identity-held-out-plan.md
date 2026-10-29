# Identity held-out evaluation: runnable, truth audit blocked

Status: 2026-10-29. Issue [#7](https://github.com/pavelkrotkov/film-iq/issues/7)
remains open. Five real specialty observations are frozen; four complete
Wikidata searches supplied eight candidate leads. One candidate-detail request
returned HTTP 429. **Zero independently audited TMDB identities are available.**
Precision, coverage, review rate and candidate recall remain **undefined**, not
zero. This execution does not validate the 99% goal in `plan.md` or close A4.

## Frozen sample and independent metadata evidence

Selection preceded resolver execution. The five purposive cases cover the two
previous leads, a short documentary with similar-title distractors, an original
language title and an incomplete artist credit. This is a convenience cohort;
it is neither representative nor evidence for population precision. The two
Deren films are correlated. No resolver rules were changed or tuned.

| Observation | Primary evidence and locator | Preserved issue |
| --- | --- | --- |
| La Jetée | [Criterion distributor record](https://www.criterion.com/films/329-la-jet-e), Film Info / Credits, 1963, Chris Marker, 27 minutes | The previous [EIDR lead](https://ui.eidr.org/content/10.5240/99A5-516D-3EE3-3838-7DCE-W) and Wikidata use 1962. The original observation stays 1963; the discrepancy is unresolved. |
| Meshes of the Afternoon | [IDFA festival archive](https://www.idfa.nl/en/film/ff61f1ef-4571-4e23-8385-5cc765d94a4d/meshes-of-the-afternoon/), header / Director, 1943, Maya Deren and Alexander Hammid, 14 minutes | Preserve both directors. Wikidata supplies a different name form for Hammid; no forced single-director match. |
| Night and Fog | [Criterion distributor record](https://www.criterion.com/films/238-night-and-fog), Film Info / Director, 1955, Alain Resnais, 32 minutes | The catalog lead supplies 1956. Similar-title candidates include films by Ann Hui, Jung Sung-il and Nagisa Ōshima. |
| LE VOYAGE DANS LA LUNE | [Cannes screening record](https://www.festival-cannes.com/en/f/le-voyage-dans-la-lune/), heading / Directed by / Year of production, 1902, Georges MÉLIES, 16 minutes | Distinguish production year from the 2011 screening. Preserve the source's director spelling, including its missing grave accent. |
| At Land | [LUX distributor record](https://lux.org.uk/work/at-land/), heading / artist / year, 1944, 15 minutes | Artist is Maya Deren, but this observation has no explicit Director field; director remains null. Candidate-detail retrieval failed, not evidence of catalog absence. |

The source pages were inspected on 2026-10-29 by Codex. The [Pompidou collection
record](https://www.centrepompidou.fr/en/ressources/oeuvre/cy9zor), inventory
AM 1987-F0125, separately corroborates Meshes' date and both creators. These
checks establish source metadata, **not the proposed TMDB IDs**. No human audit
or independent verification of a TMDB mapping is claimed.

## Candidate evidence and rights

[Wikidata structured data is CC0](https://www.wikidata.org/wiki/Wikidata:Licensing).
The small snapshot retains actual public API search responses, filtered candidate
metadata, relevant claims, entity revisions and director records. It contains no
TMDB responses, copyrighted page copies, images or catalog dump. Primary records
are represented by minimal factual observations and reproducible locators;
public access does not grant permission to reproduce their prose or images.

The policy is English `wbsearchentities` with the unmodified observed title,
50 results per page, following `search-continue`. A ten-page ceiling is explicitly
incomplete, never silently truncated. Every returned entity with a nondeprecated
P4947 (TMDB movie ID) becomes a candidate, retaining all such IDs. Other search
results are accounted for as lacking that property, not as disproven films.
Candidate titles come from en/fr/mul labels/aliases and original-title claims;
all supplied directors are joined in returned order. Multiple distinct release
years become unknown; they are not normalized to match the observation. Exact
queries, responses, entity revisions and projection policy are in
`tests/fixtures/identity/specialty-candidates.json`. This is a **Wikidata lead
search**, not a TMDB search or a claim of global catalog completeness.

The first exploratory acquisition stopped on HTTP 429 before saving a cohort.
After a pause, the retained acquisition used one second between requests and no
retries. Four searches completed with 30, 3, 12 and 8 entities respectively.
At Land's search returned two entities but its detail request received HTTP 429;
its retrieval is incomplete. Do not reinterpret its empty candidate tuple as a
successful negative search. No further live requests were made after this run.

TMDB pages were robots-blocked in the prior investigation and no API key was
available. This continuation did not retry blocked pages or use a proxy/mirror.
Public search for TMDB-specific records did not yield an independently auditable
catalog record. Wikidata external-ID assertions remain leads; they supply
neither independent truth nor proof that TMDB has the same year/director/alias.
All five truth IDs are therefore null. API access and rights must be established
before a TMDB search comparison; consult the current
[TMDB API FAQ](https://developer.themoviedb.org/docs/faq) and applicable terms.

## Run and inspect

From the `a7` worktree, the evaluation is offline and uses the retained snapshot:

```sh
UV_CACHE_DIR=.cache/uv uv run --no-sync python -m film_iq.identity.evaluation \
  tests/fixtures/identity/specialty-observations.json \
  tests/fixtures/identity/specialty-candidates.json
```

The checked-in-location artifact `docs/identity-held-out-results.json` records the
actual execution, per-case decisions, dataset version, input hashes, Git revision
and hashes of the evaluator/resolver/model code. The changes are uncommitted;
the Git revision alone does not identify the new evaluator.

Live acquisition is opt-in and must write to a new local destination inside this
project so it does not overwrite the frozen sample or a subsequent truth audit:

```sh
UV_CACHE_DIR=.cache/uv uv run --no-sync python -m film_iq.identity.wikidata_sample \
  tests/fixtures/identity/specialty-observations.json \
  .cache/identity-candidates-new.json
```

No credential is needed for this CC0 lead search. Failures are recorded as
incomplete without retries. Do not refresh while rate-limited. Reacquisition can
change the cohort; it is not necessary to rerun the offline evaluation. The
acquisition command always initializes truth as unknown and cannot audit IDs.

## Observed results and denominators

| Count | Result |
| --- | ---: |
| Attempted observations | 5 |
| Complete lead retrievals | 4 |
| Candidate leads retained across complete retrievals | 8 |
| Incomplete retrievals | 1 |
| Unknown truth | 5 |
| Scored observations (audited truth and complete retrieval) | 0 |
| Raw resolver auto-accepts across all attempted observations | 0 |
| Raw unresolved decisions across all attempted observations | 5 |
| Scored auto-accepts / correct accepts / unresolved | 0 / 0 / 0 |

Unknown truth and incomplete retrieval overlap; their exclusion counts must not
be added. Precision is correct scored auto-accepts / scored auto-accepts; coverage
is scored auto-accepts / scored cases; review rate is scored unresolved / scored
cases. All denominators here are zero. The raw five abstentions are diagnostic
outputs, not a measured 100% review rate. Candidate recall is also undefined:
without audited truth we cannot label any candidate present, missing or correct.
Per-method and per-stratum counts and ratios are emitted even when undefined.

| Case | Candidate TMDB-ID **leads**, not accepted identities | Raw decision |
| --- | --- | --- |
| La Jetée | 662 | unresolved |
| Meshes | 27040 | unresolved |
| Night and Fog | 803, 50650, 362639, 109276 | unresolved |
| Moon | 775, 444101 | unresolved |
| At Land | unknown (detail request failed) | unresolved |

These abstentions are consistent with exact year/director matching and missing
candidate data. They do not prove the leads correct or establish identity
quality. The offline tests use explicitly synthetic IDs to verify denominator
math, errors, zero acceptance, candidate misses and exclusion behavior; those
cases never contribute to the real measurement. Acquisition checks verify
pagination/caps, HTTP 429, missing entity responses and reconstruction of every
retained candidate from the CC0 evidence.

## Remaining audit gate

Obtain authorized catalog records and independent evidence linking each work to
its TMDB ID, including director, year, format and aliases. Keep source
observations unmodified, record disagreements, evidence, reviewer and decision,
and freeze the audit before any new resolver run or tuning. Unknown cases stay
excluded. An `audited` status is an operator attestation requiring a positive ID,
reviewer and evidence; the evaluator cannot determine whether the audit was
performed correctly. Never label a Wikidata-only crosswalk audited.

Only then report precision, coverage, review rate and candidate recall on eligible
cases, still conditional on the declared retrieval policy. Authorized TMDB search
is needed to measure TMDB retrieval itself. A much larger independently audited,
representative sample is required for the 99% gate; see the sample-size discussion
in `plan.md`. No ADR or acceptance criterion is promoted to verified here.
