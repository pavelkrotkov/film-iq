# Identity held-out evaluation: blocked

Status: 2026-10-29. No real benchmark has been run. Candidate sets and
independently audited TMDB truth are not available here; auto-match precision,
coverage and review rate are **unmeasured**, not zero. This protocol does not
close issue #7 or validate the 99% goal in `plan.md`.

## Source leads and rights

The following are research leads, not a frozen sample or accepted matches:

| Lead | Independent observation | Issue to audit |
| --- | --- | --- |
| La Jetée, Chris Marker | [Criterion film page](https://www.criterion.com/films/329-la-jet-e), 1963, 27 minutes; [EIDR record](https://ui.eidr.org/content/10.5240/99A5-516D-3EE3-3838-7DCE-W), 1962, short | Resolve the year discrepancy from the original records; verify the actual TMDB candidate and any alternate title separately. |
| Meshes of the Afternoon, Maya Deren and Alexander Hammid | [Criterion article](https://www.criterion.com/current/posts/8173-maya-deren-on-16-mm), 1943, 14 minutes | Check co-director representation and verify the actual TMDB candidate. |

The linked pages are used as pointers for manual verification; no page text or
catalog data is copied into a fixture. Access does not establish permission to
redistribute their content. [Wikidata structured data is CC0](https://www.wikidata.org/wiki/Wikidata:Licensing)
and may supply small attributed metadata records, but its external-ID statements
are leads, not independent verification of a TMDB record. TMDB's
[API FAQ](https://developer.themoviedb.org/docs/faq) describes noncommercial use
and attribution; check the current applicable API terms, retention and
redistribution permissions before recording candidate responses. No TMDB API
credential was present in the environment and direct film pages were blocked by
robots.txt during this investigation. Do not bypass those restrictions.

## Reproducible execution once access and rights are established

1. Before inspecting resolver outputs, select and freeze a small cohort from
   independent specialty-film source pages, including shorts, alternate titles,
   similar titles and incomplete observations. Record selection rules, dates,
   source URLs and exact locators. Avoid the synthetic development fixtures and
   do not cherry-pick known successes. Preserve supplied years and directors,
   including disagreements and multiple directors; do not silently normalize
   them into agreement.
2. For every observation obtain the actual candidate set through an authorized
   catalog search, capturing query, date, returned IDs, metadata and whether the
   response was complete. A failed or partial search is unknown, not an empty
   set. Include all returned candidates within the documented search policy;
   do not hand-select only the expected film. Retain only material whose rights
   permit the chosen storage and publication, with attribution and expiry if
   required. Record reproducible pointers or hashes where retention is barred.
3. Separately audit the correct TMDB ID against the source and catalog records,
   using director, year, format, alternate title and other independent evidence.
   Record evidence, discrepancies and reviewer; mark ambiguous or unverifiable
   truth unknown rather than inventing a match. Freeze the truth before running
   `film_iq.identity.resolve`. Keep truth out of candidate construction.
4. Run each frozen observation and full candidate tuple through `resolve` using
   `uv run python` from the repository root. Save decisions and counts with the
   dataset version and code revision. Unknown truth and failed retrievals must
   be reported separately and excluded from scored denominators, never treated
   as correct or incorrect. Report exclusions and total attempted cases.
5. On cases with audited truth and complete candidate retrieval, report counts and
   ratios: precision = correct auto-accepted / all auto-accepted; coverage =
   all auto-accepted / scored cases; review rate = unresolved / scored cases.
   If no auto-accepts exist, precision is undefined. Report raw results per case,
   method and stratum, including whether truth was absent from candidates.
   This is resolver performance conditional on retrieval; also report retrieval
   failures and true-ID candidate recall separately. A small convenience sample
   cannot establish population precision or the 99% gate. A meaningful claim
   requires a larger independently audited, representative sample; see the
   sample-size discussion in `plan.md`.

No benchmark script or fixture is added until real candidate inputs and audited
truth are available; synthetic cases in `tests/test_identity.py` remain unit
tests and are not real-world evidence.
