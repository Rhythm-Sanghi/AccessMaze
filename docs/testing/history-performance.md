# Bounded history loading

Project summaries now aggregate in one SQLite query. History uses `run.history`
with metadata-only pages (default 50, maximum 100); graphs and evidence load with
`run.get` only when a user inspects a run. The existing `run.list` remains available
for older clients. Invalid limits, offsets and unknown query fields are rejected.
Frontend request generations prevent an earlier project's response from replacing
the current page. Pagination uses native buttons and supports keyboard operation.

## Reproduce the storage measurement

```powershell
uv run --project engine python scripts/history_benchmark.py --output dist/History-review --baseline 109d90e
```

The benchmark creates explicitly synthetic SQLite records, not browser findings:
24 projects, 776 run records, a largest history of 500 runs, each with twenty
synthetic nodes and twenty controls per node. It compares the historical summary
reader from the specified commit against the current reader, verifies equal
summaries, measures actual connection counts and five warm reads, and records
three full-history/page reads, transport size and host context. Read the source
before running against a different baseline: it loads that commit's reader.

On 11 October 2026, `dist/History-after/results.json` recorded a summary median
of **479.864 ms** for the old reader and **283.906 ms** for the new reader,
with **25 connections reduced to 1**. A 500-run full response was **35,389,000
bytes**, compared with **28,007 bytes** for the first fifty summaries. These
measurements occurred on the development laptop alongside other work. Timing
varies: the earlier unchanged-reader trial had medians 376.222/340.328 ms.
Payload reduction and query count are deterministic for this workload; the timing
is not a native rendering benchmark, a peak-memory measurement, or an accepted
release performance budget. Source was dirty on `109d90e` during measurement.
