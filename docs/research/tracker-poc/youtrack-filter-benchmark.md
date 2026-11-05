# YouTrack synthetic filter measurement

On November 5, 2026, one local run used Node v26.10.0 on macOS with an x64
Node process. The uninstalled YouTrack UI candidate calls the extracted
`filterYoutrackFilms` helper for its predicate and numeric sort. Watched-only
filtering requires an available history source. It processes the same 1,000
fictional films and fictional user preferences as the Kaneo filter measurement,
mapped into YouTrack's issue and custom-field response shape. Data was already
resident in memory. Each scenario had 100 untimed warmups followed by 500
individually timed synchronous calls. Values are milliseconds per call; p95 is
the 475th sorted sample. The script checks result counts, numeric descending
interest order, and representative unknown/filter behavior.

| Scenario | Results | Median | p95 | Maximum |
| --- | ---: | ---: | ---: | ---: |
| All films | 1,000 | 0.116 ms | 0.135 ms | 0.338 ms |
| Title search | 100 | 0.169 ms | 0.175 ms | 0.325 ms |
| Netflix and interest ≥ 8, sorted | 50 | 0.799 ms | 0.925 ms | 1.150 ms |
| Sort all by interest | 1,000 | 1.152 ms | 1.221 ms | 1.360 ms |

Repeat from the worktree root:

```sh
python3 docs/research/tracker-poc/fixture_data.py 1000 | node docs/research/tracker-poc/ui/youtrack_filter_benchmark.mjs
```

The fixture distribution, warmups, number of calls and timing method match the
[Kaneo measurement](kaneo-filter-benchmark.md), though each platform uses its
own client record representation and filtering implementation. The YouTrack
predicate reads custom fields and parses synthetic availability JSON only when
the selected filter needs it; actual issue data and native server search are not
measured. The app candidate has not been installed, so the running app does not
yet use the measured helper.

Timing excludes fixture generation and mapping, YouTrack API requests and
pagination, React and DOM work, iframe overhead, artwork, browser scheduling,
memory use and concurrent activity. This is one warmed Node run, not a browser
rendering benchmark, native tracker search benchmark, sustained-load study or
Hermes performance projection. Separate runs and workloads are not controlled
experiments; their numbers vary with the machine, runtime and workload.
