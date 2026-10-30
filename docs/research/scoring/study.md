# Critical scoring: baseline and holdout study

**Version:** 0.1 · **Reviewed:** 2026-10-29 · **Issue:** [#17](https://github.com/pavelkrotkov/film-iq/issues/17)

The initial example comparisons are synthetic. They do not measure ranking
quality, discovery value, format or geographic stability, and do not select
production weights. A broad, independently corroborated holdout is **pending**.
A real ten-film derivative-source pilot is reported below with its selection limits. This study
implements neither the production scorer nor personal preference. It follows
[plan §6](../../../plan.md#6-film-scoring-and-recommendations),
[ADR 0006](../../adr/0006-scoring-separation.md) and
[ADR 0012](../../adr/0012-empirical-gates.md).

## Signals to retain

Keep original source, author, source family, eligibility, list year, work
identity, rank/tie, publication and collection times, and revisions. Do not
collapse a source's unidentified critic into a known person. An unranked
selection supports membership, not an invented numeric rank; absence from a
list is not a negative review or proof of exposure. Track extraction,
identity, evidence disagreement and personal-prediction uncertainty separately.

Keep these reception measures in their original units, together with sample
size, timestamp, lineage and data rights:

- [Rotten Tomatoes](https://www.rottentomatoes.com/about): percentage of
  professional reviews classified positive, and number of reviews. This is a
  positivity share, not an average review score.
- [Metacritic](https://www.metacritic.com/about-us/): weighted critic-review
  score on its Metascore scale, and number of reviews; it is not RT's positive
  proportion. Underlying critic overlap with lists may be unknown.
- [IMDb](https://help.imdb.com/article/imdb/track-movies-tv/faq-for-imdb-ratings/G67Y87TFYYP6TWAV):
  weighted audience rating on its 1–10 scale and number of ratings. The
  displayed rating is not a simple arithmetic mean. [RT's Popcornmeter](https://www.rottentomatoes.com/about)
  is a different audience positivity measure and must not be equated with it.

Missing scores, counts, years, geographic origin, languages, formats and
unresolved identities stay unknown. A provider failure or insufficient
reviews is not a zero score. Do not treat RT and Metacritic as independent
when their underlying review overlap is unknown.

## Candidate baselines

Pre-register the source and time windows, work matching and duplicate policy
before examining the holdout. A critic's multiple publications and
aggregators are preserved as provenance; count a known critic once per film
in the evaluation window. Unidentified critics remain unresolved. Restrict
rank comparisons to compatible eligibility cohorts; select the ballot by a
fixed source priority chosen in advance, not by whichever rank is best.

| Variant | Rule and interpretation |
| --- | --- |
| No weights | Present independent critic count, actual ranked/unranked selections, typed festival outcomes, reception measures with units and missingness separately. No artificial overall order is implied. |
| Count | Number of distinct identified original critics who selected the work in the window. Unknown critic identity and missing ballots are reported alongside, not counted as zero or as an extra critic. |
| Rank-aware | Sum `1 / rank` for one preselected, explicitly ranked ballot per known critic and work. A tie keeps its published rank; unranked endorsements remain visible separately. This is a candidate heuristic, not an empirically justified scale. |
| Rank plus awards | Add a fixed hypothetical `0.25` per distinct prize event to the rank-aware sum in a sensitivity experiment. Selection, competition inclusion and nomination are not prizes; awards and unknown coverage stay separate in the no-weights view. The coefficient is not calibrated. |
| Reception | Compare the above alongside RT positivity, Metascore and audience measures separately, on eligible observed cases, with original units and sample sizes. Never substitute one measurement for another. |
| Illustrative 45/30/15/10 | On **fully observed** cases only, combine predeclared normalized list, one specified critic aggregate, award and audience components with 45%, 30%, 15%, 10%. Fit normalization and any transformations on training data only. Report exclusion and sparsity by group; do not impute missing signals as zero. Show the no-weights view for all candidates. |

The weighted variant's choice of one professional aggregate and normalization
is a hypothetical comparison, not a claim that distinct measures mean the
same thing or that these weights are optimal. If a measure cannot legally be
used or its historical timestamp is unknown, omit that variant from the real
comparison and report why.

## Synthetic comparison

The following values are invented to illustrate disagreements. Each row is a
complete toy data record except the explicitly unknown fields. The award value
`0` means the toy event set is known complete; it must not be inferred for a
real film. The toy list component is `min(critic_count / 4, 1)`; the critic
and audience components are the toy Metascore divided by 100 and toy IMDb
score divided by 10. Award is 0 or 1. These transformations are not trained
or calibrated.

| Fictional film | Distinct critics / known ranks | Rank-aware sum | Known prizes | Toy RT positivity (reviews) | Toy Metascore (reviews) | Toy IMDb (ratings) | Illustrative weighted value |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A | 3 / 1, 2, 3 | 1.833 | 0 | 90% (10) | 20/100 (10) | 3.0/10 (100) | 0.4275 |
| B | 2 / 1, 1 | 2.000 | 1 | 70% (30) | 90/100 (30) | 7.0/10 (200) | 0.7150 |
| C | 1 / unranked | unknown | unknown | unknown | unknown | unknown | unavailable |

Count orders A before B; rank-aware orders B before A, and the hypothetical
rank-plus-prize values are B `2.25` and A `1.833`. RT positivity orders A
above B while the toy Metascore orders B above A. The fully observed weighted
formula also orders B before A; it excludes C, so it cannot establish that C is
less important. The component view shows why rankings differ and keeps the
sparse film visible. These numbers test the comparison's arithmetic only.

## Synthetic lineage check

Run from the repository root, with the cache and temporary files kept inside
the worktree:

```sh
mkdir -p .cache/uv .cache/tmp
UV_CACHE_DIR="$PWD/.cache/uv" TMPDIR="$PWD/.cache/tmp" \
  uv run --no-project python docs/research/scoring/lineage_demo.py
```

All names and films in the script are fictional. X has two identified people,
one repeated across publications, one BFI-like aggregate, one TSPDT-like
derivative aggregate and one unidentified ballot. Y has three identified
people. The observed synthetic result is `raw={'X': 6, 'Y': 3}` versus
`independent={'X': 2, 'Y': 3}`, with one unresolved ballot. Repeating every
record leaves the identified counts unchanged. Excluding the unresolved ballot
from this **known-person count** does not mean the person or endorsement does
not exist. This demonstration does not establish production behavior.

The mechanism addresses real overlap: the same critic's 2024 selections in
[Film Comment](https://www.filmcomment.com/best-films-of-2024-individual-ballots/)
and [Slant](https://www.slantmagazine.com/features/the-25-best-films-of-2024/)
share the first ten positions. A second critic's 2023 *Oppenheimer* positions
differ between Film Comment and BFI: retain both observations, but count the
critic once for breadth. Film Comment publishes only a **selection** of ballots.
BFI's source URL is `https://www.bfi.org.uk/sight-and-sound/polls/best-films-2023-all-votes`;
its terms at `https://www.bfi.org.uk/terms-use` state a deep-link restriction.
These examples establish why lineage matters, not model performance.

[TSPDT's 21st-century introduction](https://theyshootpictures.com/21stcentury.htm)
describes its index as an amalgamation of lists and ballots; its separate 2025
year-end table names several contributing publications. Agreement with such an
aggregate is not independent validation of inputs drawn from those sources.

## Unmeasured holdout lead

One proposed, narrow candidate universe is the five European Film nominees in
the [2023 European Film Academy announcement](https://www.europeanfilmacademy.org/press/main-categories-nominees-for-the-european-film-awards-2023/).
A possible source-family split would train on named individual critics from
other publications and hold out [Cineuropa's 2023 individual ballots](https://cineuropa.org/en/newsdetail/453794/),
excluding any person present on both sides. Eligibility and release windows
must be reconciled first; five award nominees cannot establish broad discovery
or geographic stability. This is a retrospective proposal, not a frozen
historical experiment or a measured holdout.

Cineuropa's [terms](https://cineuropa.org/en/aboutterms/) reserve rights and
prohibit unauthorized copying or reproduction; permission for the intended
retention and publication of ballot-derived records is unresolved. The
examined Wikipedia pages for [Anatomy of a Fall](https://en.wikipedia.org/wiki/Anatomy_of_a_Fall)
and [Green Border](https://en.wikipedia.org/wiki/Green_Border) do not supply
the individual Cineuropa poll selections needed for this split. Wikipedia's
license does not grant rights to the original publisher's pages. A separate
[BFI poll repository](https://github.com/ianrmcdonald/bfi_poll) describes
scraped ballots but presents no visible data license; neither its presence nor
republication establishes permission or makes BFI-derived votes independent.
No ballots were retained or scored. Lack of a recorded selection is unknown,
not a negative observation.

## Real 2008 pilot: observed selections and missingness

On 2026-10-30 UTC, a bounded cohort was formed from the union of Best Picture,
Best Actor and Animated Feature nominees at the
[81st Academy Awards](https://www.oscars.org/oscars/ceremonies/2009): ten distinct
films. These are award-eligibility cohorts, not a claim that every work was
produced in 2008 (*The Visitor*'s source title uses 2007). This retrospective
cohort was expanded after inspecting layouts; it is not a preregistered test.
The first five-film Best Picture-only pilot produced individual-rank data for
only *Milk* and *The Reader*, with no observations for the originally proposed
held-out Chicago Tribune critic. That pilot was inconclusive and was not
silently reported as a successful holdout.

All ten Wikipedia API requests succeeded. The retained factual observations
cover three pages: *Milk* (32), *The Wrestler* (25), and *The Reader* (4), for
61 records after audit correction. The ordinal selector initially missed
Roger Ebert's unranked *Milk* membership; an independent automated audit found
it, and the correction is retained in the dataset. The other seven pages yielded no rows through the ordinal-bullet
selector; this is **unknown coverage**, not evidence of no selections.
*The Reader*'s four records were transcribed from its factual paragraph.
Thus extraction coverage is 3/10 pages, not complete critic ballots or 100%
entry recall. Source revisions, hashes, locators, copied factual excerpts,
acquisition window and transformations are in `real_2008.json` and
[the attribution notice](REAL_DATA_NOTICE.md). The publisher's API license
declaration is retained in `wikipedia_rights.json`.

The exploratory holdout removes both known New Yorker people, David Denby
and Anthony Lane, from every training count. They were selected after seeing
the available source rows, so results are descriptive and selection-biased.
Wikipedia and the shared Metacritic intermediary are derivative carriers,
not independent critics or independent corroboration of the original ballots.
The remaining named people are counted once per work; the publication-only
*Premiere* record has unknown critic identity and is excluded. Unranked Roger
Ebert membership contributes to count but not an invented reciprocal rank.

| Film | Observed identified training people | Reciprocal-rank sum | Known held-out people | Held-out reciprocal-rank sum |
|---|---:|---:|---:|---:|
| Milk | 31 | 8.749603 | 1 | 0.142857 |
| The Wrestler | 22 | 7.809127 | 2 | 0.583333 |
| The Reader | 4 | 0.875000 | unknown | unknown |
| Seven other cohort films | unknown | unknown | unknown | unknown |

On the **two** films with observed held-out selections, count and rank both
put *Milk* first, whereas held-out rank sum puts *The Wrestler* first. Each
training top-one hits one of two known held-out-selected films: conditional
recall@1 is 1/2. Precision, exposure, complete-ballot recall, sampling error
and generalization cannot be estimated from this selected partial evidence.
The source-family labels separate the named people, but do not eliminate
the common derivative intermediary's reporting bias.

The [separate automated audit](real_2008_audit.json) independently matched
all 60 original records against the exact rendered Wikipedia revisions and
identified the additional unranked membership. It is not a human attestation
or primary-publication/critic-identity verification. It did not reproduce the
original API hashes or line numbers, and did not audit the seven unknown pages.
The Wrestler's section also has a Metacritic citation labeled **2007** despite
the section's 2008 heading; its edition lineage remains unresolved. These
limitations further restrict any inference from the conditional comparison.

A rank-plus-award sensitivity uses only the complete named event **2009 Best
Picture**, won by *Slumdog Millionaire*, with coefficient 0.25. None of the
three films with observed list data won that event, so their values and order
are unchanged. The winner's list data remain unknown; its award cannot fill
in a missing list score. This is not a count of all awards or a claim that
the other films won no prizes. The reception supplement below adds separate
descriptive variants; a full 45/30/15/10 comparison remains unavailable without
numeric audience evidence. No missing component is replaced by zero.

The no-weights output retains all ten candidates and their unknown fields.
The three observed pages concern live-action features; the three animation
nominees have unknown list observations here. Shorts and documentaries were
not sampled. Production-country context is reported below; language remains
unaudited. These gaps
preclude format/geography stability or sparse-film discovery conclusions.

Run `uv run --no-sync python docs/research/scoring/real_evaluation.py` with
the worktree-local cache environment above. The standard-library calculation
is exercised in project pytest; its assertions check the frozen denominators,
unknown rows and duplicate-insensitive identified-person arithmetic. It does
not assert that either ranking is correct. Broader original-source, identity
and period validation remain open; no production weight is chosen.

## Revision-reported reception and descriptive ablations

The same ten revisions were inspected on 2026-10-30 UTC. The source snapshots
report RT professional-review positivity and critic count for 10/10 films,
an explicit RT mean critic rating for 9/10, and Metascore plus critic count
for 10/10. These are **Wikipedia's derivative assertions**, with no original
provider request or verification. They are not contemporaneous 2008 inputs:
the cited RT/Metacritic access dates span 2008–2025 and do not establish when
the displayed numbers were measured. Acquisition dates, pinned revisions,
factual spans, reference access dates and response hashes remain separate in
`reception_2008.json`. Dynamic Kung Fu Panda average and Bolt/WALL-E RT access
dates remain unknown rather than being filled from today's templates.

| Film | RT positivity % (critics) | RT critic mean /10 | Metascore /100 (critics) | CinemaScore letter (sample size) |
|---|---:|---:|---:|---|
| Milk | 93 (245) | 8.00 | 83 (39) | unknown |
| The Wrestler | 99 (229) | 8.50 | 80 (36) | unknown |
| The Reader | 63 (202) | 6.40 | 58 (38) | unknown |
| Benjamin Button | 72 (254) | 7.50 | 70 (37) | A− (unknown) |
| Frost/Nixon | 93 (258) | 8.00 | 80 (38) | unknown |
| Slumdog Millionaire | 91 (290) | 8.40 | 86 (36) | unknown |
| The Visitor | 89 (120) | 7.62 | 79 (29) | unknown |
| Bolt | 90 (191) | 7.20 | 67 (29) | A− (unknown) |
| Kung Fu Panda | 87 (191) | unknown | 74 (36) | A− (unknown) |
| WALL-E | 95 (258) | 8.90 | 95 (39) | A (unknown) |

RT positivity leads with The Wrestler (99%), while RT critic average and
Metascore lead with WALL-E (8.9/10 and 95/100). Milk and Frost/Nixon tie on RT
positivity and mean; Frost/Nixon and The Wrestler tie on Metascore. The machine
output uses explicit tied score groups, with alphabetical labels inside each
group carrying no ranking significance. The single named-award baseline ranks
Slumdog Millionaire first and ties the other nine as non-winners of that event.
Count, reciprocal rank and rank-plus-event continue to have only three scored
films. Different orders describe different measures and coverage, not quality
improvement or independent validation.

No numeric audience score with vote denominator was observed. CinemaScore
letters are categorical observations; they are not converted to a 1–10
audience scale, substituted for votes or inserted into the full weighted
formula. That formula therefore has **0/10** fully observed films.

An explicitly **audience-omitted ablation**, rather than the original formula,
renormalizes the remaining 45/30/15 weights by 90. Its list component is
identified training count divided by the observed training-only maximum 31;
its critic component is the reported Metascore divided by 100, and its award
component is the named event's 0/1 indicator. It is descriptive on mixed-date
facts, not a temporal backtest. A second ablation drops both audience and award,
renormalizing 45/30 by 75. Neither imputes a missing list observation.
The underlying RT/Metacritic critic membership is unknown and may include the
held-out New Yorker people. Reception and these ablations are therefore not
independent holdout features or validation of predictive performance.

| Film | Audience-omitted ablation | List/critic-only ablation |
|---|---:|---:|
| Milk | 0.776667 | 0.932000 |
| The Wrestler | 0.621505 | 0.745806 |
| The Reader | 0.257849 | 0.309419 |
| Seven other cohort films | unknown | unknown |

Both ablations preserve the three-film training order and its disagreement
with the two-film observed held-out rank order. That is neither calibration
nor evidence for these weights. The no-weights output preserves every
candidate's source scores, counts, categorical audience data and missingness.

Source runtimes are 92–166 minutes, supporting an explicit greater-than-40
minute feature-length rule. The three animated-feature nominees have 3/3
reception records, 0/3 known list records and 0/3 complete weighted records;
the other seven feature-length films have 7/7, 3/7 and 0/7 respectively.
The source's reported country memberships are United States 9, United Kingdom
2, Germany 1 and France 1. These overlap (13 memberships across 10 films):
The Reader is Germany/US and Frost/Nixon US/UK/France. UK membership has 0/2
known lists; US 3/9; Germany 1/1; France 0/1. Country means production-country
metadata, so Slumdog's Indian story setting is not silently relabeled as its
production geography. There is no non-feature cohort, no audited language
comparison and no basis for geographic/format stability or discovery claims.

Two acquisition passes made 20 successful Wikipedia requests; recorded
request/body-read durations sum to 14.344 seconds, excluding deliberate
inter-request gaps, transcription, audit, later raw-byte capture and tool
overhead. Seven further successful pinned requests retained raw bytes for
audit; each matched its earlier response hash. No API/model bill or human
correction minutes were measured. Audit verification and its access limits
are recorded separately in `reception_2008_audit.json`. A separate automated
auditor found no transcription mismatches across all ten: three were checked
against previously captured exact rendered revisions, seven against actual
retained API bytes with matching revision IDs and original response hashes.
Earlier 403/cache-miss attempts are preserved. This verifies the Wikipedia
transcriptions, not their original-provider accuracy or historical as-of dates.

Run `uv run --no-sync python -m docs.research.scoring.reception_evaluation`
with the local cache environment above. Project pytest exercises this output,
missing-component exclusion, ablation normalization and explicit award ties.
None of these descriptive variants chooses production weights.

## Protocol for real evaluation

1. Obtain permission for original-source observations and retention; select a
   diverse audited candidate universe and document source eligibility, missing
   lists, critic identity, work resolution and the source-family lineage graph.
   Do not commit source bodies or assume public access permits extraction.
2. Freeze the training window, candidate universe, source identities and all
   features before the test period. Hold out an independently sourced critic
   family or a later period, excluding people appearing in both sides and any
   aggregates derived from the held-out material. If lineage or a feature's
   as-of time is unknown, exclude it from the independent comparison and
   report the reduction. Avoid a split that merely withholds one publication
   while keeping the same people's ballots in training.
3. Evaluate the same fixed shortlist size and eligible candidate universe for
   each method. Report recall among *known eligible held-out selections*,
   top-k hits and the denominators; for precision, use only independently
   reviewed candidates with explicit relevance judgments. An unselected title
   is not automatically a negative. Report unavailable scores and incomplete
   observations, not just the fully observed weighted subset.
4. Report film format, production country or region, original language and
   release cohort separately, including unknowns, sample sizes and sparse-film
   coverage. Report intervals or raw counts for small strata; do not claim
   geographic or format stability from missing or tiny groups. Exposure and
   actual viewer satisfaction remain unobserved unless separately measured.
5. Record correction time, rights, date and version; show disagreements and
   source lineage. Re-evaluate after identity corrections. Only measured,
   independent results can support a future scoring decision.

**Not yet run:** broad independently corroborated real-ballot holdout, provider data access and rights review,
calibration, error rates, human relevance judgments, stability by format or
geography, and any claim of improved discovery or personal satisfaction.
