# Local Windows performance baseline

Executed `uv run --project engine python scripts/readiness_benchmark.py` on
2026-10-10. Raw timings and 0.2-second summed RSS/handle samples are in
`readiness-benchmark.json`. Windows 11 build 26220, Python 3.13.9, 12 logical CPUs,
15.66 GiB RAM. Ordinary laptop background applications were present; short regression
tests also ran during the measurement. This is a baseline, not a controlled comparison.
Worker startup was measured before the subsequent permission-hardening change.

| Measurement | Observed |
| --- | --- |
| Development worker start, health response, EOF shutdown | 1.062–1.095 s, three fresh processes |
| Headless Chromium launch | 62.08–64.72 ms, three warm-cache samples |
| New context and local navigation | 109.20–112.49 ms |
| Sequential fixture journeys | 60, all expected statuses: 24 complete, 36 deliberately defective failures |
| Median journey by fixture | accessible 1.582 s; broken 1.767 s; errors 1.212 s; recovery 1.100 s; branch 2.396 s |
| Persistent browser soak | 181.04 s, 88 real page reloads and field edits |
| Summed RSS | peak 421.74 MiB; sample median 396.06 MiB |
| Median report generation | HTML 0.227 ms; JSON 0.166 ms; CSV 0.024 ms |
| History/project loading | maximum 182.125 ms across the growing test workspace |
| Synthetic directed graph build/path/serialization | 1k nodes 4.617 ms; 10k 34.651 ms; 50k 214.587 ms |

Graph loads are generated backend scaling probes, not observed browser states or UI
render measurements. RSS counts shared pages once per process and includes this Python
harness, driver and owned children. Short peaks do not prove a leak. The deliberately
broken/error/recovery fixtures are expected to fail their assertions; failures are not
silently converted to successful runs. Existing packaged/native startup measurements
remain recorded separately in engineering status.

Repeat the command on AC power with a documented power profile, after closing unrelated
applications, and preserve the original JSON before replacing it. `--runs 500
--soak-seconds 3600` extends the bounded probe. Before qualification, run an overnight
worker/UI soak, monitor post-run idle memory and handles, repeat cancellation/crashes,
measure native startup and large-history graph rendering, and set reviewed budgets on
representative hardware. No overnight stability, memory-leak clearance, or release
performance pass is claimed by this five-minute execution.
