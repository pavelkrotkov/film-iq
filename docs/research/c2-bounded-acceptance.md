# C2 bounded manual-cohort acceptance assessment — 2026-10-31

**Decision submitted for review:** accept the existing bounded Phase-1 manual source expansion under [C2 #20](https://github.com/pavelkrotkov/film-iq/issues/20), subject to the controller's source-specific approval, independent PR reviews and CI. This assessment does not itself accept the issue. The issue's preference for small rights-verified cohorts over an automated 2010–2026 scrape is unchanged; broader backfill remains conditional work.

## Factual review

At main `e9c383e`, a fresh **independent automated/agent-assisted alignment review** checked all **24 cohorts and 114 accepted observations** against the reviewed manifests, CSVs and prior independent original-source/primary-identity audits. Complete raw contexts and normalized observation/source columns agreed: title, director, position, rank/tie, listed year, locator, source URL/family, eligibility and identity provenance. All scoped counts and accepted/valid revisions matched their independent completeness attestations. Publication fields, document revisions and scope metadata remained explicit rather than inferred.

All **112 resolved mentions matched the prior independently reviewed decisions**, representing exactly **106 catalog work IDs**. Both unresolved cases remained unresolved. Every reviewed typed classification and award category/recipient/outcome/unknown-date payload matched its prepared evidence. The [original 2022 Library of Congress announcement](https://blogs.loc.gov/now-see-hear/2022/12/announcing-the-2022-national-film-registry/) additionally corroborated the 25 chronological entries and the separate Best Actor person prize; the controller independently repeated that primary check. No correction was needed.

This reused valid automated source audits rather than re-fetching every source. It is case-by-case evidence inspection, **not human labor, a blinded identity truth set or a general accuracy estimate**. Private per-observation receipts label the automated reviewer and retain factual provenance without source-page copies or personal data.

A native SQLite private-copy replay of all 24 unchanged imports returned the same accepted revisions and added zero extraction revisions, observations, match decisions or classifications. The canonical typed-component/scorer document was identical and foreign-key checks passed. Actual database bytes/semantics and selected source-input hashes remained unchanged. Earlier actual-import and historical-snapshot replay checks remain valid; unfamiliar layouts are not accepted unattended.

## Source-specific approval submitted for review

[ADR 0011](../adr/0011-cost-rights.md) governs access, retention, attribution and redistribution. All 24 manifests attest allowed use for their declared manual scopes. The proposed approval is limited to the existing local factual records and private research, not general Gate B or provider adoption.

| Existing scope | Permitted basis and boundary |
| --- | --- |
| Five Senses of Cinema contributor ballots; 47 facts | Recorded private-study/research basis; minimal manual factual records only. No broad crawl, source-derived cohort redistribution, publisher prose/images/page copies or invented retention duration. |
| Two Library of Congress Registry editions and one historical performance-prize context; 51 facts | Recorded government-authored factual-record CC0 policy. Third-party films, images and essays remain outside that basis. |
| Sixteen Wikidata date-qualified award statements | CC0 main-namespace structured facts, independently primary-corroborated; derivative awards, never critic votes. Other/undated claims remain outside scope. Festival references stay private; no public-link/page-copy permission inferred. |
| Existing 106-work catalog display | Attributed bounded TMDB metadata retains its original 2027-04-29 deadline and no training/evaluation use. No new acquisition, catalog dump or implied endorsement. |

Final adjudication must explicitly accept these **source/use-specific manual decisions**. It cannot grant a later source, method, retention or bulk-expansion permission. General [Gate B](gate-b.md) remains qualified by its original research, including **3/8 held-out complete documents**.

## Existing acceptance criteria

| #20 criterion | Bounded evidence and disposition |
| --- | --- |
| Expand only cohorts approved at Gate B | Exact manual-use decisions above are proposed for controller acceptance. No whole-Gate-B barrier replaces source-specific review; broader rights/provider decisions remain open. |
| Preserve rank/tie, eligibility, document revision and source family | All 114 normalized observations/raw contexts and all 24 manifests agree with reviewed inputs. Published ranks remain separate from alphabetical, bullet and chronological positions. Source-listed, eligibility, release and award years remain distinct. |
| Track unmatched films and review uncertain cases, including shorts | Prior case-by-case agent-assisted primary review and fresh independent alignment preserve short-work director aliases, translated titles, same-title exclusions and date disagreements. One experimental film and one home-movie collection remain unresolved and visible; no forced film/year substitution. This is automated reviewer inspection, not a human-only oracle. |
| Publish year/geography/format coverage and review/failure volume | The [coverage report](c2-bounded-coverage.md) publishes scoped source editions, release-year counts, nonexclusive geography/language, explicit formats, request/candidate windows and known access hurdles. Unknowns remain explicit: 64 works lack geography/language collection; 83 lack explicit format labels. |
| Replay without duplicated votes | All 24 unchanged imports retain identical revisions and component/scorer semantics. Fifty Registry selections and seventeen awards stay separate from critic votes; acquisition attempts are distinct from semantic evidence. |
| Prioritize rights-verified individual critic, typed award and specialty/translated sources | Five original individual ballots, two preservation editions and primary-corroborated derivative awards provide the selected diversity. Performance-prize context retains its person recipient. No aggregate becomes a critic vote. |
| Track edition, method, completeness, contributor and lineage | Five complete contributor scopes remain partial publisher coverage; two 25-entry Registry editions are complete; seventeen award contexts remain partial. Named-critic/original-ballot links preserve dependence semantics. |
| Independently validate each source, rank/tie/category and IDs | Prior independent source/primary-ID audits and the new 114-row check cover every selected scope and current decision. The held-out parser result is not generalized to unfamiliar layouts. |
| Measure actual reviewer effort before a bulk/backfill work estimate | **Not triggered:** no human bulk/backfill estimate is proposed. Human minutes/throughput remain unknown; agent/API timing is not substituted. A future estimate requires actual measurement first, not a retroactive human re-audit of otherwise supported bounded cohorts. |

## Acceptance boundary

The **47 critic observations retain verified original normalized lineage**. The **67 noncritic observations retain unknown normalized legacy lineage fields**, alongside separately reviewed typed classifications and descriptive original/derivative audits. No direct retagging or historical rewrite occurred. These rows never enter the critic-vote calculation; any generic lineage correction requires versioned review history.

The recommendation is bounded MVP acceptance **once the specific approvals and reviews above are accepted**, with new bulk ingestion, automated broad historical backfill and human bulk-labor estimation still conditional on their own evidence and permissions. Unresolved identities, incomplete coverage and unknown exact award dates remain visible. This neither claims complete 2010–2026 coverage, calibration or user satisfaction, nor changes the separate personal, provider, planner, recovery or conditional upstream-Movary contracts.
