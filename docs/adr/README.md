# Architecture decision records

ADRs document what is *decided*, what is deliberately *provisional*, and which evidence can change it. Do not convert a provisional assumption to a dependency without recording its gate result.

| ADR | Decision | Status |
|---|---|---|
| [0001](0001-movary-ownership.md) | Movary remains personal system of record | Accepted |
| [0002](0002-python-sqlite.md) | Python modular monolith and local SQLite | Accepted |
| [0003](0003-film-identifiers.md) | TMDB operational identity and reviewable unmatched sources | Accepted |
| [0004](0004-typed-provenance.md) | Typed original evidence, corrections and independent families | Accepted |
| [0005](0005-extraction-choice.md) | Simple extraction first; optional tools benchmarked | Provisional |
| [0006](0006-scoring-separation.md) | Separate critical importance and personal prediction | Accepted; weights provisional |
| [0007](0007-movary-ratings-export.md) | Complete ratings via existing CLI export, API for history | Accepted for POC |
| [0008](0008-availability-providers.md) | TMDB baseline, head-to-head free provider evaluation | Provisional |
| [0009](0009-bundle-optimization.md) | Explicit utility, entitlement and no-purchase option | Accepted policy; calibration provisional |
| [0010](0010-interface-scope.md) | CLI/report, not a new Movary replacement | Accepted |
| [0011](0011-cost-rights.md) | Zero-new-fee target and rights-aware persistence | Accepted |
| [0012](0012-empirical-gates.md) | Measure before committing advanced dependencies | Accepted |

