# Original publisher CSV supplement

Checked 2026-10-30 UTC for [B3 / #13](https://github.com/pavelkrotkov/film-iq/issues/13),
under plan §4's extraction hierarchy and measured pilot. This is a development
format supplement, separate from the frozen 32-section Wikipedia cohort and
holdout. It is one original publisher resource, not 25 independent documents,
and does not establish general spreadsheet or unseen-publisher accuracy.

## Publisher, scope and rights

CNC's [named dataset](https://www.data.gouv.fr/datasets/6311c164ebfb165ddc828ded)
identifies the **Centre national du cinéma et de l'image animée** as producer,
with certified/public-service publisher badges in its API metadata, and explicitly
assigns **Licence Ouverte / Open Licence 2.0** to this dataset. Its resource list
identifies CSV **1c5075ec-7ce1-49cb-ab89-94f507812daf**, describes the file as visa
files jointly conserved by CNC and Archives nationales, and links the exact
[native CSV](https://static.data.gouv.fr/resources/liste-des-visas-dexploitations-cinematographiques-delivres-de-1945-a-2025/20251113-091845/liste-des-films-sortis-dans-les-salles-de-cinema-en-france-de-1945-a-2025.csv).
The rights basis is this explicit declaration for the dataset containing this
named resource, rather than an inference from government hosting. There is no
separate resource-level override in the captured metadata.

[Licence Ouverte 2.0](https://www.data.gouv.fr/pages/legal/licences/etalab-2-0)
permits copying, extraction, transformation and redistribution worldwide for an
unlimited duration, with source and last-update attribution. Attribute:
**Centre national du cinéma et de l'image animée (CNC), Liste des visas
d'exploitations cinématographiques délivrés de 1945 à 2025, updated
2025-11-13, Licence Ouverte 2.0**, with the dataset link above. This reuse is
not endorsed by CNC. The retained factual rows contain no film images, criticism
or copied films; the declaration grants no right to the films themselves.

These are administrative visa records, not critical endorsements, streamable
catalog entries or proof of present availability. Preserve the displayed title,
director and `Date` verbatim; `Date` has no verified release/premiere/production
semantics here. `Non renseigné` remains a raw unknown value. Visa IDs identify
administrative files, not TMDB works. Film identity stays null; titles sharing
text are not merged. Format is a source category, display position is a locator,
and neither rank nor ties are inferred.

## Acquisition and complete bounded selection

`source_receipt.json` records the exact URL, UTC time, HTTP status, bytes, hash,
headers, resource ID and explicit selection. The ordinary source request returned
**200**, **12,821,667 bytes**, SHA-256
`61674d72814c60789a1f04b7ef93bfba9ee39033cbc4ade26b3bfe03daec2e91`
at `2026-10-30T04:30:26.273359+00:00`, taking **39.719523 seconds** including
response reading and local writes. The full native CSV and captured publisher
metadata remain only in `.cache/tabular/` inside this worktree. The publisher's
resource update is 2025-11-13; the response's Last-Modified is 2026-10-20.
These distinct metadata dates do not establish new film observations.

A full strict CSV scan counted **95,764 logical data records**, each with nine
cells. The retained `source-window.csv` is a byte-exact native prefix containing
the entire header and **logical data records 1–25 inclusive**; there is no
filtering or resorting. In this particular window the records also occupy
physical lines 2–26. It is **3,522 bytes**, SHA-256
`a7d6a0fd081daef6a2aeb089181c253733873a0204631836489d8c5fcda0288a`.
The prefix was checked against the logical-record selection from the complete
original. Only completeness of this explicitly bounded window is benchmarked;
no full-dataset extraction completeness is claimed.

The source uses UTF-8 with BOM, semicolon delimiters and CRLF record endings.
The standard library reader uses strict CSV parsing and preserves Unicode,
nonbreaking spaces, trailing spaces, accents and every selected field's raw
value. It rejects changed headers, unexpected width and missing/extra records.
A fixed source hash requires a new audit after any source revision.

## Reproduction and boundaries

From the B3 worktree root:

```sh
UV_CACHE_DIR="$PWD/.cache/uv" TMPDIR="$PWD/.cache/tmp" \
  uv run --no-sync python -m docs.research.extraction.tabular.csv_baseline
```

The runnable check compares every selected observation field against a separate
original-source row audit and rejects an omitted final record. Native CSV needs
neither browser rendering, LLM extraction nor a new dependency: use stdlib CSV for
this resource. The experiment does not benchmark XLSX, arbitrary delimiter
inference, quoted multiline records, malformed CSV recovery or a production
incremental adapter. A failure is review-required, never an empty successful list.
Acquisition labor, correction minutes, resource cost and long-term maintenance
remain unmeasured. A single local timing cannot establish performance superiority.
