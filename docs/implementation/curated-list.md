# Curated-list import (#59)

Use a manually selected **single source edition and ballot** rather than a
publisher scraper. This command creates no watchlist, rating or watched-history
writes:

```sh
uv run python -m film_iq.ingest.curated_command --csv path/list.csv --manifest path/list.json
# Explicit pending persistence; independent extraction acceptance is separate:
uv run python -m film_iq.ingest.curated_command --csv path/list.csv --manifest path/list.json --persist data/evidence.db
```

The first command is a dry run. It prints every candidate, published rank/tie,
identity status, source scope and total/reviewed-identity/unresolved/accepted/
watched-excluded counts. `accepted=0` describes this import's pending extraction,
not a claim to independently checked source evidence. Python callers can supply
`watched_tmdb_ids` from the complete personal snapshot; omission does not assert
that films were unwatched. The full C7 integration and real-user demonstration
remain separate acceptance work.

CSV header order is exact:

```csv
source_id,source_url,edition,ballot_scope,position,rank,tie,published_at,eligibility_date,raw_title,director,year,tmdb_id,identity_reviewer,identity_evidence,locator
```

Blank rank/year/director/date/ID values stay unknown. Position is a unique source
locator ordinal and may have gaps in a deliberate selection; it never supplies a
missing rank. Dates require an exact ISO day; month-only dates stay blank and
belong in the manifest's attribution/context. A supplied TMDB ID requires both a
named reviewer and work-identification evidence. It is a manual assertion, not an
automatically verified identity. Keep ambiguous works without IDs. The importer
records reviewed crosswalks in the existing reversible match-decision ledger;
unresolved rows remain in the extraction and preview.

The JSON manifest mirrors `ingest.curated_manifest.CuratedList`: `policy` contains
all `SourcePolicy` fields (`id`, `name`, `url`, `family`, `independence_group`,
`access`, `retention`, `redistribution`, `attribution`); other keys are `edition`,
`ballot_scope`, `document_revision`, `eligibility`, `completeness`, `scope`,
`lineage`, `rank_semantics`, `rights_status`, `rights_evidence`, `permitted_use`
and `expected_count`. Declare `completeness` as `complete` or
`intentionally_partial`; a complete selected ballot is still partial publisher
coverage. Include ballot identity in `edition` so different ballots never share
one edition key. Unknown contributors must remain identified as unknown rather
than being invented from the publisher name. Independence group is an explicit
reviewed lineage key, never inferred. Derivative records retain their underlying
ballot identity; scoring determines whether evidence can be independently counted.

`rights_status=allowed` is a recorded caller attestation, not a permission grant.
Resolve the exact intended use first. Nonblank policy and rights evidence are
required before opening a database; unknown/blocked rights reject persistence.
No full publisher page, prose, images, private scores or provider catalog belongs
in committed CSV fixtures. Rights records are retained with the extraction.

Unchanged input replays the same semantic revision and identity decision. Changed
facts create a new pending revision and preserve the accepted predecessor.
Independent review uses the existing `ingest.accept.accept` API and a complete
`AuditAttestation`, explicitly naming the expected previous accepted revision.
A repeat import never silently promotes or replaces accepted evidence.

## Bounded live cohort, 2026-10-30

BFI's source registry still records unresolved copying/retention/deep-link rights;
this implementation grants none. An alternative original Senses of Cinema
World Poll 2023 contributor ballot supplies a private ten-film factual research
cohort, scoped to one named contributor and one new-film list. No source-derived
cohort is committed. Its About policy, retrieved through the web reader on
2026-10-30, permits private study/research copying but prohibits copying for other
individuals and publication without author permission. This supports only the
bounded private research use; no public redistribution, general crawler, or
unlimited retention permission is claimed. The separate controller's About-page
request redirected to a suspended page: current availability is inconsistent.

Private input/manifest/report artifacts remain in the approved project's ignored
`.cache/epic-c/curated/`. Exact source ranks/years are retained, including a source
release year differing from an external premiere year. Independent source and ID
review, integration with the current real personal snapshot and C7 report are
required before #59 closes. No identity precision, discovery quality, entitlement
or overall source completeness is established by parser tests.
