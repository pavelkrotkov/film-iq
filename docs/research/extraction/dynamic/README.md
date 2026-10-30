# Supplemental dynamic interface: Wikidata Query Service

This is one real JavaScript interface using a deliberately defined two-entity
query, separate from the frozen 32-section publisher corpus. It tests retrieval
paths, not critic-list representativeness, identity precision or unseen layouts.
The retained structured results are CC0 under [Wikidata's licensing policy](https://www.wikidata.org/wiki/Wikidata:Licensing).
No interface HTML, script assets or images are redistributed.

```sparql
SELECT ?film ?filmLabel WHERE {
  VALUES ?film { wd:Q553901 wd:Q640561 }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
} ORDER BY ?film
```

On 2026-10-30 UTC, an automated Brave browser entered the query into the
[official interface](https://query.wikidata.org/) and used its Execute control.
The rendered table showed both requested entity IDs with the English labels
recorded in `browser.json`. The interface reported two results in 1,336 ms.
The separately recorded 41,632 ms until inspection includes model/tool delay
and is not query runtime. Browser setup, network-request count and billed
model cost were not measured.

Two subsequent identified stdlib HTTP requests returned 200. The initial
17,940-byte interface HTML contained neither displayed result label as literal
text; its hash and this bounded check are recorded without retaining the HTML.
The interface's Code → URL control exposed its public `/sparql` endpoint.
One request to that endpoint with `Accept: application/sparql-results+json`
returned 601 bytes containing the same two IDs/labels. Exact query, endpoint,
UTC times, byte counts and SHA-256 hashes are in `receipts.json`. The 0.286 s
HTML and 0.222 s JSON request timings are single sequential observations;
different caches and timing boundaries prevent a fair speed comparison.

The browser supplied the dynamic view, but the documented HTTP JSON API
supplied the same data without browser rendering. Prefer that native API for
this bounded query. This does not establish that an API exists for another
publisher, validate Crawl4AI or supply an original publisher spreadsheet.
Neither surface independently corroborates the other's underlying facts.
Human correction effort and general maintenance costs remain unmeasured.

Repeat the UI query by pasting the SPARQL above into the official interface.
Repeat the HTTP request using the exact URL and Accept header in the receipt;
future labels/results may change. The retained observation can be checked
offline from the worktree root:

```sh
UV_CACHE_DIR="$PWD/.cache/uv" TMPDIR="$PWD/.cache/tmp" \
  uv run --no-sync python -m docs.research.extraction.dynamic.check
```

The check verifies the saved response hash and exact agreement with the
observed two-row browser table. It does not launch a browser, repeat the live
query, prove general HTML completeness or claim an independent human audit.
