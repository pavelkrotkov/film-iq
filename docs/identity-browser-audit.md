# Issue #7: automated browser truth audit

Checked **2026-10-30 UTC** by **automated:Codex-browser**. The parent operator,
separate from the resolver implementation authors, directly inspected public TMDB
records in the actual user browser. Earlier webfetch requests were robots-blocked;
the browser was accessible. This implementation records the parent-supplied facts,
not another inspection. This is an **automated operator audit**, not independent
human review or calibrated accuracy. Independent GPT evidence-adequacy review is
pending; issue #7 and Gate A remain open. The 99% precision target is unverified.

The [truth-only overlay](../tests/fixtures/identity/specialty-browser-truth.json)
retains minimal visible facts, locators, both source URLs and comparison judgments.
Primary facts are the frozen observations from 2026-10-29, not new primary-page
retrievals. Mapping judgments use title, creator and work context, rather than
Wikidata crosswalk agreement alone. `audited` is the existing evaluator's operator
attestation status; the evaluator cannot establish evidence adequacy.

| Work / visible TMDB record | Frozen primary comparison | Operator judgment |
| --- | --- | --- |
| [La Jetée, 662](https://www.themoviedb.org/movie/662-la-jetee): 1962, Chris Marker Director, 29m | [Criterion](https://www.criterion.com/films/329-la-jet-e): La Jetée, 1963, Chris Marker, 27m | Same title/creator and short-work context; retain year/runtime disagreement. |
| [Meshes of the Afternoon, 27040](https://www.themoviedb.org/movie/27040-meshes-of-the-afternoon): 1943, Maya Deren Director/Writer and Alexander Hammid Director, 14m | [IDFA](https://www.idfa.nl/en/film/ff61f1ef-4571-4e23-8385-5cc765d94a4d/meshes-of-the-afternoon/): same title/year, both directors, 14m | Both directors corroborated; do not simplify credits or rewrite Wikidata's different name form. |
| [Night and Fog, 803](https://www.themoviedb.org/movie/803-nuit-et-brouillard): 1956, Alain Resnais Director, 32m | [Criterion](https://www.criterion.com/films/238-night-and-fog): Night and Fog, 1955, Alain Resnais, 32m | Title/creator and short-documentary context distinguish the similar-title leads; retain year disagreement. |
| [A Trip to the Moon, 775](https://www.themoviedb.org/movie/775-le-voyage-dans-la-lune): 1902, Georges Méliès Director, 15m | [Cannes](https://www.festival-cannes.com/en/f/le-voyage-dans-la-lune/): LE VOYAGE DANS LA LUNE, 1902, Georges MÉLIES, 16m | Translated title/creator and 1902 short-work context support the mapping; preserve title/name forms and runtime disagreement. |

No original observation, candidate, retrieval record or saved result is replaced.
No resolver or production evaluator changes or tuning are included. No provider
pages, images, prose copies or catalog dumps are retained. At Land has no overlay:
truth stays unknown and its failed candidate-detail retrieval stays incomplete.
Missing evidence is not catalog absence.

The [new results](identity-browser-audit-results.json) score exactly four cases:
zero auto-accepts, coverage 0/4 = **0**, review rate 4/4 = **1**, conditional
candidate recall 4/4 = **1**, precision **undefined** (no accepted matches).
At Land is excluded for both unknown truth and incomplete retrieval; these
overlapping exclusions must not be added. These are four purposive convenience
cases, not population estimates. Recall is conditional on the **existing Wikidata
lead retrieval policy**, not TMDB search or full-catalog recall. Browser facts are
audit evidence only and never replace the candidate metadata given to `resolve()`.
The original [held-out report](identity-held-out-plan.md) and its zero-scored
artifact remain the historical unaudited run.

Reproduce offline from this worktree (the existing sibling environment is used
without syncing it; all project output remains here):

```sh
PYTHONPATH=src ../a4/.venv/bin/python - <<'PY'
import copy
import hashlib
import json
from pathlib import Path

from film_iq.identity.evaluation import evaluate

fixtures = Path("tests/fixtures/identity")
paths = [fixtures / f"specialty-{name}.json"
         for name in ("observations", "candidates", "browser-truth")]
contents = [path.read_bytes() for path in paths]
sample, catalog, overlay = map(json.loads, contents)
assert overlay["version"] == sample["version"]
truths = {case["id"]: case["truth"] for case in overlay["cases"]}
patched = copy.deepcopy(catalog)
for case in patched["cases"]:
    case["truth"] = truths.get(case["id"], case["truth"])
report = evaluate(sample, patched)
report["audit"] = overlay["audit"]
report["input_sha256"] = {
    str(path): hashlib.sha256(content).hexdigest()
    for path, content in zip(paths, contents, strict=True)
}
report["code_sha256"] = {
    name: hashlib.sha256(Path("src/film_iq/identity", name).read_bytes()).hexdigest()
    for name in ("evaluation.py", "matching.py", "models.py")
}
Path("docs/identity-browser-audit-results.json").write_text(
    json.dumps(report, ensure_ascii=False, indent=2) + "\n"
)
PY
```

The three input hashes bind the original cohort and separate audit, and code hashes
identify the unchanged production implementation from base `56dd306`. The single
regression checks saved-result replay, denominators, At Land exclusion, unchanged
in-memory inputs and original file bytes:

```sh
mkdir -p .cache/tmp
TMPDIR="$PWD/.cache/tmp" PYTHONPATH=src ../a4/.venv/bin/python -m pytest \
  tests/test_identity_browser_audit.py --basetemp=.cache/pytest-browser-audit
```

Local verification: 293 tests passed, one opt-in live test skipped; Ruff check,
format check, ty and diff checks passed. Radon over all 108 source/test Python
files reports maximum CC 8 and minimum MI 50.025; the new regression file has
maximum CC 5 and MI 69.380. No live Movary call or watchlist write was performed.
