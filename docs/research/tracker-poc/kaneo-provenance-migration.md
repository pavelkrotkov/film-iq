# Kaneo provenance privacy remediation

New private-input imports write the same category-neutral provenance for every
film. Exact original provenance stays in the ignored source manifest. The
separate migration previews by default and, with an explicit `--apply`, only
replaces current values that exactly match the old importer-generated values.
Any edited or missing value makes that film a conflict; a partly completed
migration can be rechecked and resumed. Titles, lifecycle, source evidence,
preferences and the input manifest are not changed. Run one importer at a
time without concurrent editing: the Kaneo API has no compare-and-swap, so a
change between the final read and write cannot be ruled out. A failed request
must be inspected before retrying.

In a fictional local test, changing custom fields added no events to the task's
activity API. This is not proof of erasure. Earlier values may still exist in
PostgreSQL storage, WAL, backups or snapshots; their retention and removal have
not been assessed. No real-data migration has been performed by these checks.

On 2026-11-05 the separate local POC migration updated all 130 matching records
with zero conflicts. The source manifest's hash was unchanged, a repeat updated
zero records, and readback verified neutral current fields, unchanged source
evidence and review links, and denial to an unrelated viewer. These results do
not change the historical-storage limitation above.
