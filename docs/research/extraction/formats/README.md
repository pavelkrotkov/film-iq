# Supplemental original-source PDF experiment

Checked 2026-10-30 UTC for [B3 / issue 13](https://github.com/pavelkrotkov/film-iq/issues/13).
This is an additional development-format check, separate from the frozen
32-section Wikipedia cohort and its holdout. It is not an unseen-publisher
holdout or a general PDF, OCR, spreadsheet or festival-programme benchmark.

## Source and rights

The Library of Congress's [historical alphabetical National Film Registry PDF](https://www.loc.gov/static/programs/national-film-preservation-board/documents/Registry-Titles-alphabetically.pdf)
states that it lists selections from **1989–2017**. Only its entire first page
is in scope: alphabetical display positions, title, displayed release year
and registry-induction year. Display order is not critical rank. This is a
government selection list, not an independent critic ballot or a current
streaming catalog.

The [Library's copyright guidance](https://www.loc.gov/legal/security-copyright-and-privacy/understanding-copyright/)
states that works produced by its employees within their duties are generally
public domain and makes Library US-government works available worldwide under
CC0. The retained material is the Library's factual Registry table, with no
film images, criticism or third-party essays. This basis does not grant rights
to the films, images or other collections. Attribute the factual source to
the Library of Congress, National Film Preservation Board.

One identified ordinary HTTP request returned **200** at
`2026-10-30T03:19:25.107792+00:00`: 207,602 bytes, SHA-256
`a3029ab9dbe880e5f904e48b263eb5d42c53c204cb137269d3a95f5584dd37c8`.
The original twenty-page PDF remains uncommitted in the worktree cache.
`registry-page1.pdf` is a standalone first-page copy made by PDFKit, not the
original HTTP body; its separate hash and transformation are recorded in
`source_receipt.json`. No text was edited. The server's Last-Modified header
is retrieval metadata and does not update the document's stated 2017 scope.

## Independent expectation and measured outcome

The separate automated auditor visually enumerated the original first-page
render without reading PDF text extraction, parser output, tests or expected
data. `pdf_audit.json` records its method, all **36** expected records,
receipt/hash checks and limits. It is not a human audit or independent
corroboration of the original film identities. The release value for
*The Augustas* is `1930s-1950s`, preserved as a displayed range; release and
Registry-selection years remain separate fields.

Native macOS PDFKit text extraction followed by a bounded standard-library
line selector returned **36/36 exact records**, including titles, both year
fields, positions, null ranks and category. The whole-page comparison passed.
One native run, including process startup, parsing and comparison, took
0.305462 seconds. The offline saved-text check took 0.000943 seconds. These
are single local runs, not performance comparisons. Acquisition labor,
auditor correction minutes and resource cost were not measured. No OCR,
browser rendering, model API or added Python package was needed for this
born-digital page.

Reproduce from the B3 worktree root, using the existing environment:

```sh
UV_CACHE_DIR="$PWD/.cache/uv" TMPDIR="$PWD/.cache/tmp" \
  uv run --no-sync python -m docs.research.extraction.formats.pdf_baseline
```

The live local extraction requires macOS `osascript` and PDFKit. On other
systems the default command reports unknown and exits 2; no PDF dependency
is installed automatically. The cross-platform snapshot comparison is:

```sh
UV_CACHE_DIR="$PWD/.cache/uv" TMPDIR="$PWD/.cache/tmp" \
  uv run --no-sync python -m docs.research.extraction.formats.pdf_baseline --snapshot
```

That mode checks the retained text-extraction snapshot, not the system's PDF
extractor. Both modes verify the retained PDF hash and compare every field
against the independent visual oracle. A changed PDF is unknown and needs a
new audit; an incomplete or disagreeing extraction fails. The runnable check
also asserts that an omitted final row cannot pass completeness.

## Other acquisition outcomes

The Canadian federal [NFB online-title dataset](https://open.canada.ca/data/en/dataset/deeaddd4-fa52-4fd7-9668-d66940280493)
is indexed with an Open Government Licence–Canada declaration. Its description
warns that some listed titles cannot be viewed because of rights restrictions.
The linked original resource host `opengov.nfb.ca` failed DNS resolution on
ordinary authorized requests for robots.txt and its dataset README at
`2026-10-30T03:17:57Z`; no CSV or ZIP was acquired. The portal and licence URLs
returned 403 in the web reader. This candidate's CSV extraction and specific
resource rights remain unverified; no absence or availability conclusion
follows. No streaming catalog dump is retained or committed.

An older LOC women-directors PDF lead returned 404 in the web reader. No
content or empty-list result was inferred. The original-source PDF measured
above is a different verified document. Original CSV/XLSX and browser-only
formats remain unmeasured by this supplement.
