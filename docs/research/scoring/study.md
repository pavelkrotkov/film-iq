# Critical scoring: baseline and holdout study

**Version:** 0.1 · **Reviewed:** 2026-10-29 · **Issue:** [#17](https://github.com/pavelkrotkov/film-iq/issues/17)

The example comparisons below are synthetic. They do not measure ranking
quality, discovery value, format or geographic stability, and do not select
production weights. A real independent holdout is **pending**. This study
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

**Not yet run:** real-ballot holdout, provider data access and rights review,
calibration, error rates, human relevance judgments, stability by format or
geography, and any claim of improved discovery or personal satisfaction.
