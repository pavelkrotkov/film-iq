# Audited suggestion library

The November 20, 2026 expansion adds 1,538 films to the existing Kaneo project,
bringing the collection to 1,668 films. Source observations remain in Film IQ's
SQLite evidence ledger. Movary supplies current personal history and ratings.

The private source collection contains 2,249 factual selections across 278
declared source editions or ballot scopes.

| Source collection | Editions or scopes | Observations | Declared coverage |
| --- | --- | --- | --- |
| Annual polls and five named critic ballots | 32 | 1,100 | Complete selected editions or first ballot lists, spanning 2010–2025 and published 2026 midyear selections |
| National Film Registry | 37 | 925 | Every class from 1989–2025, with 25 selections per class |
| Official festival award slices | 69 | 81 | Selected Venice, Rotterdam, IDFA and CPH:DOX award categories and years, including co-winners |
| Wikidata festival award statements | 132 | 135 | Partial coverage of original festival editions |
| Wikidata Annecy short-film awards | 8 | 8 | Partial coverage of original festival editions |

There are 1,624 distinct matched films in these source collections. Another
277 source observations retain unresolved identities. Collections, combined-film
selections, conflicting years and published attribution errors remain visible
in the private source records. Ten newly matched films have no TMDB poster.

## Import and publication

`film_iq.source_library` accepts a version-one JSON bundle with `sources` and
`audits`. Each source carries the existing `SourcePolicy`, `CuratedList` manifest
fields and exact curated CSV entry fields. Independent audits bind the complete
normalized source to its SHA-256 fingerprint. The parent source observations and
their original URLs, references and statement identifiers are preserved under
`provenance`.

```sh
uv run python -m film_iq.source_library private/reviewed-library.json \
  --database private/evidence.db --output private/source-library.json
```

All editions publish in one database transaction. A failed edition leaves the
previous current extractions intact. Replays reuse semantic revisions and match
decisions. A changed award category or outcome receives a new revision through
the optional `recognition_context` checksum input. Existing imports with an empty
context retain their earlier checksum calculation.

The generated library index works through the existing discovery `--cohort`
entry point. Acceptance and identity are re-read from the ledger. Named critics
use shared contributor keys across publications. Award outcomes, registry
selections and critic selections retain separate types. Aggregate polls preserve
their dependence on underlying ballots.

`docs/research/sources/build_catalog.py` corroborates supplied IDs or source
titles and directors against TMDB movie details. Search results propose
candidates. Ambiguous and combined works remain unresolved. Staged display data
has a seven-day deadline, and an expired record is refreshed on replay.
`prepare_library.py` joins the independent source audits and current identity
results into the import bundle.

The existing Kaneo integration is recorded in
`docs/research/sources/kaneo-library.patch`. The deployment uses the same project
and Tailscale URL, the existing supported Kaneo task importer, seven-day metadata
cache, daily ratings refresh and macOS startup job. Public IMDb/TMDB/Wikidata
crosswalks can supply ratings independently of artwork availability.
Film details include each source's original title, year and director alongside
the reviewed display, and typed award categories, outcomes and recipients.
These facts are joined by their accepted source entry and revision identifiers.

## Verification and remaining coverage

The complete collection loaded across 17 board pages. Independent desktop and
iPhone-sized checks found 1,633 recommendations and 29 films in the Watched
view, with watched films excluded from recommendations. New film details passed
poster decoding, genre, score, original evidence and inline Movary form checks.
These browser checks blocked personal writes. Source-library replay added zero
observations, extraction revisions, audit records or match decisions.

`library_check.py` exercises complete counts, unresolved identities, independent
review binding, all-edition rollback, unchanged replay and award-only corrections.
The existing suite passed with 199 tests and one opt-in integration skip.
Batching source evidence reduced the discovery builder from 31 seconds to under
one second on the expanded collection. Final live insights reads took
0.73–1.60 seconds in the independent check.

Annual coverage is complete for the declared editions. Every publisher's full
historical archive and every festival category remain broader research scopes.
The Rosenbaum canon's three web parts have now passed independent original-page
audit after 39 field corrections: 993 visible selections against an advertised
1,000. The unexplained seven-selection gap and grouped works remain explicit.
These additions are still undergoing canonical identity checks and are not
included in the live counts above. Matching now checks complete paged search
results and published aliases; earlier partial-search receipts cannot bypass
the new review. Audience ratings remain sparse in Wikidata. The
configured MDBList credential still returned HTTP 403 on November 20, 2026.
Missing scores retain their unknown state and prior verified values survive
partial or failed refreshes.

The source-specific research is recorded in
[annual lists](../research/sources/annual-expansion-20261120.md),
[festivals and preservation](../research/sources/festival-expansion-20261120.md)
and [critics and ratings](../research/sources/ratings-expansion-20261120.md).
