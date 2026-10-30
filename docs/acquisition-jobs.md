# Durable acquisition attempts

C1 adds operational bookkeeping to the existing extraction acceptance path. It
introduces no crawler, scheduler, external request or provider adoption. Migration
009 preserves historical `source_run` keys: those identify semantic revisions,
not individual fetches. Rollback requires restoring a pre-upgrade backup; older
versions deliberately refuse a version-9 database. No evidence table is rewritten.

The scheduled single writer uses these APIs:

1. `acquisition_policy.set_permission()` records the existing `SourcePolicy`,
   permitted acquisition method, allowed/blocked decision, rights evidence,
   reviewed UTC time and optional retention deadline. Unknown permission is
   blocked. This is a recorded review decision, not automatic legal validation.
2. Commit any caller transaction, then call `acquisition.begin_attempt()`. Its
   committed UUID identifies this attempt, records the previous successful cursor
   and freezes the permission metadata in force. A blocked/expired source fails
   before an attempt starts. Use the method reviewed in the permission record.
3. Fetch using an already approved adapter. Use existing `persist()` to stage a
   complete extraction and commit it. Unchanged documents/extractions retain the
   same semantic IDs. Failed/partial requests must never invoke acceptance.
4. Call `finish_attempt()` with UTC finish time and `success`, `partial`, `error`
   or `unknown`. Success requires a same-source stored extraction revision and
   atomically updates the last successful cursor. It does **not** accept evidence.
   Other outcomes cannot carry a cursor/revision and leave the successful cursor
   unchanged. Store short nonsecret error codes, never exception bodies or tokens.
5. Existing `accept()` and independent audit/replacement rules promote a pending
   revision. Matches remain independently reviewed and reversible through the
   existing identity decision log.

`acquisition_status()` supplies the CLI/report with latest attempt outcome,
attempt/finish times, safe error code, permission state, retention deadline and
last successful cursor/time separately. No attempt means unknown, not success.
A killed process leaves a committed `running` attempt; explicitly finish it as
`unknown`/`interrupted`, then begin a new attempt. SQLite rolls back unfinished
semantic transactions. Restart never infers an absent film or source removal.

`ballots.record_ballot()` and `link_entry()` attach stable edition/list → ballot →
entry links. The publisher stays on `published_list.source_id`. An optional
reviewed contributor key can identify the same person across publishers;
unknown contributors remain null. Derivative ballots can link to an original
ballot without inventing independent critics. Scope, original ranks/ties and
partial/unranked semantics stay in their existing observation/list records.
Ballot metadata is immutable: conflicts require review rather than overwrite.

Offline tests cover upgrade from schema 8, failed/partial attempts, permission
expiry, atomic cursor updates, abrupt process exit/restart, repeated successful
fetches, explicit accepted revision replacement and ballot lineage. They are not
live publisher-rights, extraction accuracy or production recovery validation.
C8 owns actual expiry/deletion, complete installation restore and deployment.
