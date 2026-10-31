# Typed public recognition

Public selection evidence, awards and reception measurements remain separate;
none becomes the user's enjoyment/artistic-merit score or an opaque weighted
quality score. `critic_selection` alone can enter current critic aggregation.
`institutional_selection`, `registry_selection`, `award_outcome` and
`reception_metric` retain their own original facts and source links. Unknown
classification is not a critic vote.

Curated manifests may declare `evidence_kind` as a selection kind. Omission is
`unknown`, preserving compatibility without guessing the publisher's role.
The kind is part of the curated record fingerprint: a type-only correction
creates a new pending extraction rather than retagging the accepted predecessor.
The usual independent source audit must verify the type before acceptance.
Legacy accepted records remain unclassified until an explicit independent review.
No migration guesses type from source name, author, publisher or family.

For source entries requiring structured award/reception facts, reuse the existing
extraction, work matching and independent acceptance APIs. Before acceptance,
`recognition.storage.classify_entry` attaches a typed `Selection`, `AwardOutcome`
or `ReceptionMetric` and a `ClassificationReview`. The review requires exact
boolean independent/allowed assertions, evidence, attribution/use context and a
timezone-aware review time. These are recorded assertions, not a rights grant.
An initial unreviewed unknown declaration can be explicitly classified; known
classifications are immutable. Changed known facts need a new extraction revision
and independently accepted replacement, preserving current accepted evidence.
An unchanged unknown manifest replay preserves any separately reviewed typed
annotation and its original review; the placeholder is not a request to retract
the annotation. Changed source content or an explicit manifest kind still creates
a new pending revision.

A same-kind tuple can hold several metrics/outcomes from one original source
entry without manufacturing extra entries. Canonical payloads deduplicate exact
facts. Selection, competition, nomination and prize remain distinct; awards
preserve category, recipient and recipient type. A Best Actor performance prize
must identify its person recipient and cannot silently become Best Film. Unknown
ceremony edition/date stays null even when the citing page has a known date.

Reception values preserve source measure label, critics/audience population,
metric type, original unit and observed sample count. Positivity percentages,
mean scores, numeric counts and categorical grades have different types/units.
Missing values or counts stay null. Booleans, numeric strings for numeric values,
nonfinite numbers, invalid ranges and fractional/negative sample counts reject
before storage. No unit conversion, guessed sample size or calibrated weight is
introduced. Rights-uncleared real reception data must remain absent/unknown.

`recognition.components(db, tmdb_id)` reads current accepted observations
through accepted work identities. Unresolved source facts remain per-entry in
component snapshots and discovery review cards; they never establish a film
match or merge distinct unknown films. A public lookup with a null TMDB ID
returns empty component arrays and missing coverage; unresolved facts must be
addressed by their explicit entry/revision elsewhere. It exposes separate component arrays, unknown
classifications and explicit missing coverage alongside source/document/revision/
match links, publication/measurement dates and lineage. Detailed classification
rights/auditor assertions remain in the database instead of cluttering reports.

`recognition.snapshot.save(db)` stores a canonical
`recognition-components-v1` document containing current typed facts and the
separate current critic outputs. Repeating identical state returns the same ID;
`replay` preserves that frozen document after corrections. Existing critic
`independent-reciprocal-rank-v1` and `independent-priority-rank-v2` snapshots retain
their existing replay algorithms. No historical snapshot is reinterpreted. Source-listed release years, source
eligibility and source family remain explicit. Snapshot catalog release year is
unknown: the expiring external display catalog is not copied into indefinite
component snapshots. The discovery presentation separately offers bounded
release-cohort views from its fresh reviewed catalog dates; it never substitutes
a source edition or source-listed year for a catalog release date.

Markdown groups choices into critic lists, festival/award recognition,
preservation/institutional selections and other source selections. Each work
appears once in its first applicable view with all its reasons; this changes no
JSON ordering, score or source fact. Order within a section follows the existing
suggestion list. The source-support ordering sentence applies only to eligible
critic choices with known support; unknown support is never zero.

Discovery cards retain their title/director/runtime and source reasons. Known
registry/institutional selections and explicit award recipients/categories can
appear as concise reasons. Full reception units/sample counts, dates, missingness
and component provenance remain in the expandable audit and JSON. The planning
report also shows accepted typed facts; registry-only works have unknown critic
utility and are never assigned an invented zero or automatic award weight.

Migration011 adds classification and component-snapshot tables; existing rows
remain unknown. Use the normal private SQLite backup/migration/restore workflow.
