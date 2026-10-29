# Issue #6: captured-page adapter deliverable — 2026-10-29

Implemented in `.worktrees/a6` only. No commit, push, GitHub mutation, configuration change, or Epic B access. The four existing legacy transcriptions/excerpts remain unchanged.

## Evidence and scope

Four distinct Wikipedia pages are captured as **unmodified MediaWiki API section responses**, not manual transcriptions or whole-page HTML snapshots. Both raw wikitext and separately rendered HTML responses are retained. `tests/fixtures/ingest/pages/captures.json` records exact endpoints, status, retrieval times, response sizes and SHA-256 hashes; `*.revision.json` records pinned revision IDs/timestamps. Image URLs/markup appear in the rendered evidence; no image bytes were fetched.

| Page / captured section | Revision | Actual records | Semantics |
| --- | --- | ---: | --- |
| NBR 2022 / Top 10 Films | 1269459635 | 11 | Best Film ranked 1; ten additional alphabetical, unranked selections |
| NBR 2023 / Top 10 Films | 1370562803 | 10 | Best Film ranked 1; nine additional alphabetical, unranked selections |
| Sight and Sound 2012 / Directors' poll | 1196879962 | 10 | Explicit ranks, ties at 2 and 7; partial aggregate |
| Sight and Sound 2022 / Directors' poll | 1332699136 | 11 | Explicit ranks, ties at 4, 6 and 9; all three at rank 9 retained |

The two new adapters (`nbr_pages`, `sight_sound_pages`) accept only these frozen bytes. They preserve raw selection rows, exact line locators, display position, rank, ties, section scope, edition eligibility and derivative lineage. Changed, empty, error or truncated responses fail with review required. These are deliberately frozen POC adapters, not general live parsers. Existing persistence now accepts their output and preserves tie IDs and rank semantics. Unchanged ingestion creates no further database changes. No adapter resolves film identity or invents detailed eligibility.

## Independent audit, acceptance and original sources

`independent-fixture-audit.json` is the unedited report of a **separate ephemeral read-only automated agent** (gpt-6.1-sol). It inspected rendered HTML, revision evidence, capture receipts and the license declaration; it was explicitly excluded from wikitext captures, adapters and tests. Its 42 expected records were produced before the adapters and are the test oracle. This is independent automated verification of the captured derivative pages, not a human attestation or independent upstream confirmation. Acquisition and development used the same main agent; the alternate HTML rendering is not independent critical evidence.

All real fixture extractions remain `provisional` / `pending`, with no `current_extraction` promotion and no fabricated `AuditAttestation`. Issue #6 requires independent audit, not specifically human audit. The independent automated oracle plus tested capture/revision/rights evidence satisfies the audit scope of the 42 derivative-page records. Its kind is automated; this is not a human attestation. The original report’s “pending human audit” wording reflects the implementing agent’s mistaken instruction to that subagent, not an issue requirement. The original report is preserved unedited as evidence; this clarification supersedes its human-only gating language. A subsequent explicit, accurately scoped independent automated attestation can use the existing acceptance path. Machine-readable lineage verification remains at the schema's unknown default; textual derivative lineage is retained. Do not treat these as independent NBR/BFI votes.

The primary NBR 2023 announcement was read and its Best Film plus all nine alphabetical Top Films checked. The correct NBR 2022 announcement was found by search and its Best Film plus ten alphabetical Top Films checked. The BFI 2022 original directors' list was read: its ranks 1, 2, 3, =4, =6, 8, =9 agree with the captured 11-film excerpt. These checks were performed by the implementing agent, not the independent audit agent. They corroborate selection/rank facts, not full eligibility, original ballots, film identity or permission to redistribute the primary publications.

The BFI 2012 page initially timed out through the web reader. Direct HTTP succeeded; a follow-up inspection removed script/style blocks in memory and corroborated **all ten titles, positions, ranks and tie groups**, plus vote counts, against the upstream Directors’ top 100. See `bfi-2012-corroboration.json` for the factual records, response hash, byte count and limitations. The upstream director/year labels conflict with image-caption years for Mirror (1974/1975) and Bicycle Thieves (1949/1948); no normalization or identity acceptance was inferred. This follow-up was performed by the implementing automated agent, separately from the independent derivative-page oracle. It completes upstream title/rank corroboration for the 2012 subset, not a full source/eligibility/identity audit. No restricted upstream page bodies were retained.

**Partial distinction:** both Sight and Sound captures contain the complete published Wikipedia directors' section but only part of the original top-100 aggregate. Neither is an individual ballot. NBR publishes institutional selections, with underlying ballot completeness unknown. **No genuine partial individual-ballot fixture has been acquired.** Film Comment's selective publication of ballots does not itself prove that any displayed ballot is incomplete. This deliverable covers ranked/tied/unranked/partial-aggregate cases; it does not satisfy the partial-individual-ballot acceptance case, and issue #6 remains open.

## Rights

See `tests/fixtures/ingest/pages/NOTICE.md`. The retained text is Wikipedia derivative evidence under its recorded CC BY-SA 4.0 declaration, with contributor attribution via each pinned article and history. Preserve that license for the copied text and adaptations. The code remains MIT. This does not license BFI/NBR original pages, criticism, referenced publications, or images. The independent expected-record report derives from the same Wikipedia material and is distributed under CC BY-SA 4.0 as well.

## Validation

Full suite: **93 passed** (29 new parametrized cases). Ruff check and format check pass. `ty check --python ../a5/.venv/bin/python .` passes with A6 `src` on PYTHONPATH. A6's existing environment lacked pytest/quality tools; A5's environment was used read-only, without installation or configuration changes. UV cache and pytest temporary databases stay under A6. The initial default ty environment failed to resolve pytest; selecting the actual tool environment resolved it.

Radon was executed from the explicitly requested `../a5/.venv/bin/radon` over **all `src` and `tests` Python files**, not only changed files. Final exact results and commands are in `validation.json`. Maximum CC is 8 and minimum MI is 50.03; both requested limits pass. Coverage is complete only for the 42-record automated oracle cohort; this is not a claim about live pages, held-out layouts or independently audited upstream precision.

## Access record and remaining work

`access-attempts.json` lists exact exploratory endpoints and observed outcomes; retained successful requests are exhaustively enumerated in the capture receipts. No unsuccessful request was treated as source absence. Sandbox DNS denial was resolved with authorized network access; an unidentified/encoded API request's 403 was resolved by the identified User-Agent and previously working URL form. Missing/redirecting titles and a guessed NBR URL were abandoned for verified alternatives. No further access retries are needed to use this deliverable.

Remaining acceptance evidence: a rights-cleared actual partial individual ballot and broader issue/PR integration and review. The 2012 title/rank subset is now upstream-corroborated; conflicting year labels and film identity remain unresolved. No acceptance checkbox or empirical gate was marked complete. Human acceptance is optional, not an issue requirement.

## Minimal attestation correction

The existing implementation used human-only prose in `audit.py`, `accept.py`, the capture review message and migration 008’s historical comment. That was an implementation assumption, not an issue requirement. Runtime `validate_audit()` checks auditor/evidence/time, independence, completeness and a positive count; `accept()` additionally checks stored count and explicit replacement. Neither checks that an auditor is human.

The scoped fix removes the misleading module/message wording and updates its assertion. No acceptance logic, SQL migration or state transition changes are needed to submit an accurately labelled automated attestation. Use an explicit auditor identity such as `automated:<agent/run identity>` and put structured evidence in the existing `evidence` string, including `auditor_kind: automated`, report/capture hashes, reviewed scope and limitations. A human attestation must instead identify `auditor_kind: human`; an unlabelled historical record must remain kind unknown, never inferred human. Both auditor and evidence are persisted verbatim. A dedicated kind column would improve typed querying but is a separate schema change, not a prerequisite for honest attestation here.

No actual acceptance call or attestation was fabricated in this deliverable. The frozen `review_reason` now says that explicit acceptance has not been recorded, rather than demanding a human reviewer. The original independent oracle’s `human_audit: false` remains correct.
