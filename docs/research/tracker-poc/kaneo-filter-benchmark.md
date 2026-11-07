# Kaneo synthetic filter measurement

On November 5, 2026, one local run used Node v26.10.0 on macOS with an x64
Node process. It measured the exact `filterFilms` function used by the Kaneo
UI, with 1,000 generated fictional films and one fictional user's preferences
already resident in memory. Each scenario had 100 untimed warmups followed by
500 individually timed synchronous calls. Reported values are milliseconds
per call; p95 is the 475th sorted sample. The script checks result counts and
numeric descending interest order before measuring.

| Scenario | Results | Median | p95 | Maximum |
| --- | ---: | ---: | ---: | ---: |
| All films | 1,000 | 0.060 ms | 0.066 ms | 0.216 ms |
| Title search | 100 | 0.069 ms | 0.072 ms | 0.215 ms |
| Netflix and interest ≥ 8, sorted | 50 | 0.643 ms | 0.759 ms | 1.111 ms |
| Sort all by interest | 1,000 | 1.065 ms | 1.142 ms | 1.330 ms |

Repeat from the worktree root:

```sh
python3 docs/research/tracker-poc/fixture_data.py 1000 | node docs/research/tracker-poc/ui/filter_benchmark.mjs
```

The fixture is deterministic; provider and interest combinations follow its
synthetic distribution. The provider scenario includes parsing the stored
synthetic availability JSON. Timing excludes fixture generation and initial
mapping, API requests and pagination, React and DOM work, posters and other
images, browser scheduling, memory use, and concurrent activity. This is a
single warmed Node run, not a browser-rendering benchmark, a sustained-load
study, a comparison with YouTrack, or a performance projection for Hermes.
Actual timings can vary with runtime, machine and workload.
